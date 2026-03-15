from abc import ABC, abstractmethod
import inspect
from typing import Any, List, Dict, Optional, Tuple, Pattern, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
from enum import IntFlag, auto
from crawl4ai import ExtractionStrategy
from crawl4ai.config import (
    CHUNK_TOKEN_THRESHOLD,
    OVERLAP_RATE,
    WORD_TOKEN_RATE,
)
from crawl4ai.utils import *  # noqa: F403

from crawl4ai.utils import (
    sanitize_html,
    escape_json_string,
    perform_completion_with_backoff,
    extract_xml_data,
    split_and_parse_json_objects,
    sanitize_input_encode,
    merge_chunks,
)
from crawl4ai.models import * # noqa: F403

from crawl4ai.models import TokenUsage

from crawl4ai.model_loader import * # noqa: F403
from crawl4ai.model_loader import (
    get_device,
    load_HF_embedding_model,
    load_text_multilabel_classifier,
    calculate_batch_size
)

from crawl4ai.types import LLMConfig, create_llm_config

from functools import partial
import numpy as np
import re
from bs4 import BeautifulSoup
from lxml import html, etree

from crawl4ai.prompts import PROMPT_EXTRACT_BLOCKS_WITH_INSTRUCTION, PROMPT_EXTRACT_SCHEMA_WITH_INSTRUCTION, PROMPT_EXTRACT_BLOCKS, PROMPT_EXTRACT_INFERRED_SCHEMA
from custom_crawler.prompts import PROMPT_EXTRACT_GIST


###################################################################
#  Strategies using GIGACHAT LLM-based extraction for text data   #
###################################################################

DEFAULT_PROVIDER = "gigachat/GigaChat"
DEFAULT_PROVIDER_API_KEY = "GIGACHAT_CREDENTIALS"

class GigaExtractionStrategy(ExtractionStrategy):
    """
    A strategy that uses an LLM to extract meaningful content from the HTML.

    Attributes:
        llm_config: The LLM configuration object.
        instruction: The instruction to use for the LLM model.
        schema: Pydantic model schema for structured data.
        extraction_type: "block" or "schema".
        chunk_token_threshold: Maximum tokens per chunk.
        overlap_rate: Overlap between chunks.
        word_token_rate: Word to token conversion rate.
        apply_chunking: Whether to apply chunking.
        verbose: Whether to print verbose output.
        usages: List of individual token usages.
        total_usage: Accumulated token usage.
    """
    _UNWANTED_PROPS = {
            'provider' : 'Instead, use llm_config=LLMConfig(provider="...")',
            'api_token' : 'Instead, use llm_config=LlMConfig(api_token="...")',
            'base_url' : 'Instead, use llm_config=LLMConfig(base_url="...")',
            'api_base' : 'Instead, use llm_config=LLMConfig(base_url="...")',
        }
    def __init__(
        self,
        llm_config: 'LLMConfig' = None,
        extract_gist=True,
        instruction: str = None,
        schema: Dict = None,
        extraction_type="block",
        chunk_token_threshold=CHUNK_TOKEN_THRESHOLD,
        overlap_rate=OVERLAP_RATE,
        word_token_rate=WORD_TOKEN_RATE,
        apply_chunking=True,
        input_format: str = "markdown",
        force_json_response=False,
        verbose=False,
        # Deprecated arguments
        provider: str = DEFAULT_PROVIDER,
        api_token: Optional[str] = None,
        base_url: str = None,
        api_base: str = None,
        **kwargs,
    ):
        """
        Initialize the strategy with clustering parameters.

        Args:
            llm_config: The LLM configuration object.
            instruction: The instruction to use for the LLM model.
            schema: Pydantic model schema for structured data.
            extraction_type: "block" or "schema".
            chunk_token_threshold: Maximum tokens per chunk.
            overlap_rate: Overlap between chunks.
            word_token_rate: Word to token conversion rate.
            apply_chunking: Whether to apply chunking.
            input_format: Content format to use for extraction.
                            Options: "markdown" (default), "html", "fit_markdown"
            force_json_response: Whether to force a JSON response from the LLM.
            verbose: Whether to print verbose output.

            # Deprecated arguments, will be removed very soon
            provider: The provider to use for extraction. It follows the format <provider_name>/<model_name>, e.g., "ollama/llama3.3".
            api_token: The API token for the provider.
            base_url: The base URL for the API request.
            api_base: The base URL for the API request.
            extra_args: Additional arguments for the API request, such as temperature, max_tokens, etc.
        """
        super().__init__( input_format=input_format, **kwargs)
        self.llm_config = llm_config
        if not self.llm_config:
            self.llm_config = create_llm_config(
                provider=DEFAULT_PROVIDER,
                api_token=os.environ.get(DEFAULT_PROVIDER_API_KEY),
            )
        self.instruction = instruction
        self.extract_type = extraction_type
        self.schema = schema
        self.extract_gist = extract_gist
        if schema:
            self.extract_type = "schema"
        self.force_json_response = force_json_response
        if extract_gist:
            self.force_json_response = False
        self.chunk_token_threshold = chunk_token_threshold or CHUNK_TOKEN_THRESHOLD
        self.overlap_rate = overlap_rate
        self.word_token_rate = word_token_rate
        self.apply_chunking = apply_chunking
        self.extra_args = kwargs.get("extra_args", {"ssl_verify": False})
        if not self.apply_chunking:
            self.chunk_token_threshold = 1e9
        self.verbose = verbose
        self.usages = []  # Store individual usages
        self.total_usage = TokenUsage()  # Accumulated usage

        self.provider = provider
        self.api_token = api_token
        self.base_url = base_url
        self.api_base = api_base

    
    def __setattr__(self, name, value):
        """Handle attribute setting."""
        # TODO: Planning to set properties dynamically based on the __init__ signature
        sig = inspect.signature(self.__init__)
        all_params = sig.parameters  # Dictionary of parameter names and their details

        if name in self._UNWANTED_PROPS and value is not all_params[name].default:
            raise AttributeError(f"Setting '{name}' is deprecated. {self._UNWANTED_PROPS[name]}")
        
        super().__setattr__(name, value)  
        
    def extract(self, url: str, ix: int, html: str) -> List[Dict[str, Any]]:
        """
        Extract meaningful blocks or chunks from the given HTML using an LLM.

        How it works:
        1. Construct a prompt with variables.
        2. Make a request to the LLM using the prompt.
        3. Parse the response and extract blocks or chunks.

        Args:
            url: The URL of the webpage.
            ix: Index of the block.
            html: The HTML content of the webpage.

        Returns:
            A list of extracted blocks or chunks.
        """
        if self.verbose:
            # print("[LOG] Extracting blocks from URL:", url)
            print(f"[LOG] Call LLM for {url} - block index: {ix}")

        variable_values = {
            "URL": url,
            "HTML": escape_json_string(sanitize_html(html)),
        }

        prompt_with_variables = PROMPT_EXTRACT_BLOCKS
        if self.extract_gist:
            prompt_with_variables = PROMPT_EXTRACT_GIST
        if self.instruction:
            variable_values["REQUEST"] = self.instruction
            prompt_with_variables = PROMPT_EXTRACT_BLOCKS_WITH_INSTRUCTION

        if self.extract_type == "schema" and self.schema:
            variable_values["SCHEMA"] = json.dumps(self.schema, indent=2) # if type of self.schema is dict else self.schema
            prompt_with_variables = PROMPT_EXTRACT_SCHEMA_WITH_INSTRUCTION

        if self.extract_type == "schema" and not self.schema:
            prompt_with_variables = PROMPT_EXTRACT_INFERRED_SCHEMA

        for variable in variable_values:
            prompt_with_variables = prompt_with_variables.replace(
                "{" + variable + "}", variable_values[variable]
            )   

        try:
            response = perform_completion_with_backoff(
                self.llm_config.provider,
                prompt_with_variables,
                self.llm_config.api_token,
                base_url=self.llm_config.base_url,
                json_response=self.force_json_response,
                extra_args=self.extra_args,
                base_delay=self.llm_config.backoff_base_delay,
                max_attempts=self.llm_config.backoff_max_attempts,
                exponential_factor=self.llm_config.backoff_exponential_factor
            )
            # Track usage
            usage = TokenUsage(
                completion_tokens=response.usage.completion_tokens,
                prompt_tokens=response.usage.prompt_tokens,
                total_tokens=response.usage.total_tokens,
                completion_tokens_details=response.usage.completion_tokens_details.__dict__
                if response.usage.completion_tokens_details
                else {},
                prompt_tokens_details=response.usage.prompt_tokens_details.__dict__
                if response.usage.prompt_tokens_details
                else {},
            )
            self.usages.append(usage)

            # Update totals
            self.total_usage.completion_tokens += usage.completion_tokens
            self.total_usage.prompt_tokens += usage.prompt_tokens
            self.total_usage.total_tokens += usage.total_tokens

            try:
                content = response.choices[0].message.content
                blocks = None

                if self.force_json_response:
                    blocks = json.loads(content)
                    if isinstance(blocks, dict):
                        # If it has only one key which calue is list then assign that to blocks, exampled: {"news": [..]}
                        if len(blocks) == 1 and isinstance(list(blocks.values())[0], list):
                            blocks = list(blocks.values())[0]
                        else:
                            # If it has only one key which value is not list then assign that to blocks, exampled: { "article_id": "1234", ... }
                            blocks = [blocks]
                    elif isinstance(blocks, list):
                        # If it is a list then assign that to blocks
                        blocks = blocks
                elif self.extract_gist:
                    if content is None:
                        raise ValueError("Optional value is None")
                    blocks = [{"text": content}]
                else: 
                    # blocks = extract_xml_data(["blocks"], response.choices[0].message.content)["blocks"]
                    blocks = extract_xml_data(["blocks"], content)["blocks"]
                    blocks = json.loads(blocks)

                for block in blocks:
                    block["error"] = False
            except Exception:
                parsed, unparsed = split_and_parse_json_objects(
                    response.choices[0].message.content
                )
                blocks = parsed
                if unparsed:
                    blocks.append(
                        {"index": 0, "error": True, "tags": ["error"], "content": unparsed}
                    )

            if self.verbose:
                print(
                    "[LOG] Extracted",
                    len(blocks),
                    "blocks from URL:",
                    url,
                    "block index:",
                    ix,
                )
            return blocks
        except Exception as e:
            if self.verbose:
                print(f"[LOG] Error in LLM extraction: {e}")
            # Add error information to extracted_content
            return [
                {
                    "index": ix,
                    "error": True,
                    "tags": ["error"],
                    "content": str(e),
                }
            ]

    def _merge(self, documents, chunk_token_threshold, overlap) -> List[str]:
        """
        Merge documents into sections based on chunk_token_threshold and overlap.
        """
        sections =  merge_chunks(
            docs = documents,
            target_size= chunk_token_threshold,
            overlap=overlap,
            word_token_ratio=self.word_token_rate
        )
        return sections

    def run(self, url: str, sections: List[str]) -> List[Dict[str, Any]]:
        """
        Process sections sequentially with a delay for rate limiting issues, specifically for LLMExtractionStrategy.

        Args:
            url: The URL of the webpage.
            sections: List of sections (strings) to process.

        Returns:
            A list of extracted blocks or chunks.
        """

        merged_sections = self._merge(
            sections,
            self.chunk_token_threshold,
            overlap=int(self.chunk_token_threshold * self.overlap_rate),
        )
        extracted_content = []
        if self.llm_config.provider.startswith("groq/"):
            # Sequential processing with a delay
            for ix, section in enumerate(merged_sections):
                extract_func = partial(self.extract, url)
                extracted_content.extend(
                    extract_func(ix, sanitize_input_encode(section))
                )
                time.sleep(0.5)  # 500 ms delay between each processing
        else:
            # Parallel processing using ThreadPoolExecutor
            # extract_func = partial(self.extract, url)
            # for ix, section in enumerate(merged_sections):
            #     extracted_content.append(extract_func(ix, section))

            with ThreadPoolExecutor(max_workers=4) as executor:
                extract_func = partial(self.extract, url)
                futures = [
                    executor.submit(extract_func, ix, sanitize_input_encode(section))
                    for ix, section in enumerate(merged_sections)
                ]

                for future in as_completed(futures):
                    try:
                        extracted_content.extend(future.result())
                    except Exception as e:
                        if self.verbose:
                            print(f"Error in thread execution: {e}")
                        # Add error information to extracted_content
                        extracted_content.append(
                            {
                                "index": 0,
                                "error": True,
                                "tags": ["error"],
                                "content": str(e),
                            }
                        )

        return extracted_content

    async def aextract(self, url: str, ix: int, html: str) -> List[Dict[str, Any]]:
        """
        Async version: Extract meaningful blocks or chunks from the given HTML using an LLM.

        How it works:
        1. Construct a prompt with variables.
        2. Make an async request to the LLM using the prompt.
        3. Parse the response and extract blocks or chunks.

        Args:
            url: The URL of the webpage.
            ix: Index of the block.
            html: The HTML content of the webpage.

        Returns:
            A list of extracted blocks or chunks.
        """
        from crawl4ai.utils import aperform_completion_with_backoff

        if self.verbose:
            print(f"[LOG] Call LLM for {url} - block index: {ix}")

        variable_values = {
            "URL": url,
            "HTML": escape_json_string(sanitize_html(html)),
        }

        prompt_with_variables = PROMPT_EXTRACT_BLOCKS
        if self.extract_gist:
            prompt_with_variables = PROMPT_EXTRACT_GIST
        if self.instruction:
            variable_values["REQUEST"] = self.instruction
            prompt_with_variables = PROMPT_EXTRACT_BLOCKS_WITH_INSTRUCTION

        if self.extract_type == "schema" and self.schema:
            variable_values["SCHEMA"] = json.dumps(self.schema, indent=2)
            prompt_with_variables = PROMPT_EXTRACT_SCHEMA_WITH_INSTRUCTION

        if self.extract_type == "schema" and not self.schema:
            prompt_with_variables = PROMPT_EXTRACT_INFERRED_SCHEMA

        for variable in variable_values:
            prompt_with_variables = prompt_with_variables.replace(
                "{" + variable + "}", variable_values[variable]
            )

        try:
            response = await aperform_completion_with_backoff(
                self.llm_config.provider,
                prompt_with_variables,
                self.llm_config.api_token,
                base_url=self.llm_config.base_url,
                json_response=self.force_json_response,
                extra_args=self.extra_args,
                base_delay=self.llm_config.backoff_base_delay,
                max_attempts=self.llm_config.backoff_max_attempts,
                exponential_factor=self.llm_config.backoff_exponential_factor
            )
            # Track usage
            usage = TokenUsage(
                completion_tokens=response.usage.completion_tokens,
                prompt_tokens=response.usage.prompt_tokens,
                total_tokens=response.usage.total_tokens,
                completion_tokens_details=response.usage.completion_tokens_details.__dict__
                if response.usage.completion_tokens_details
                else {},
                prompt_tokens_details=response.usage.prompt_tokens_details.__dict__
                if response.usage.prompt_tokens_details
                else {},
            )
            self.usages.append(usage)

            # Update totals
            self.total_usage.completion_tokens += usage.completion_tokens
            self.total_usage.prompt_tokens += usage.prompt_tokens
            self.total_usage.total_tokens += usage.total_tokens

            try:
                content = response.choices[0].message.content
                blocks = None

                if self.force_json_response:
                    blocks = json.loads(content)
                    if isinstance(blocks, dict):
                        if len(blocks) == 1 and isinstance(list(blocks.values())[0], list):
                            blocks = list(blocks.values())[0]
                        else:
                            blocks = [blocks]
                    elif isinstance(blocks, list):
                        blocks = blocks
                elif self.extract_gist:
                    if content is None:
                        raise ValueError("Optional value is None")
                    blocks = [{"text": content}]        
                else:
                    blocks = extract_xml_data(["blocks"], content)["blocks"]
                    blocks = json.loads(blocks)

                for block in blocks:
                    block["error"] = False
            except Exception:
                parsed, unparsed = split_and_parse_json_objects(
                    response.choices[0].message.content
                )
                blocks = parsed
                if unparsed:
                    blocks.append(
                        {"index": 0, "error": True, "tags": ["error"], "content": unparsed}
                    )

            if self.verbose:
                print(
                    "[LOG] Extracted",
                    len(blocks),
                    "blocks from URL:",
                    url,
                    "block index:",
                    ix,
                )
            return blocks
        except Exception as e:
            if self.verbose:
                print(f"[LOG] Error in LLM extraction: {e}")
            return [
                {
                    "index": ix,
                    "error": True,
                    "tags": ["error"],
                    "content": str(e),
                }
            ]

    async def arun(self, url: str, sections: List[str]) -> List[Dict[str, Any]]:
        """
        Async version: Process sections with true parallelism using asyncio.gather.

        Args:
            url: The URL of the webpage.
            sections: List of sections (strings) to process.

        Returns:
            A list of extracted blocks or chunks.
        """
        import asyncio

        merged_sections = self._merge(
            sections,
            self.chunk_token_threshold,
            overlap=int(self.chunk_token_threshold * self.overlap_rate),
        )

        extracted_content = []

        # Create tasks for all sections to run in parallel
        tasks = [
            self.aextract(url, ix, sanitize_input_encode(section))
            for ix, section in enumerate(merged_sections)
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                if self.verbose:
                    print(f"Error in async extraction: {result}")
                extracted_content.append(
                    {
                        "index": 0,
                        "error": True,
                        "tags": ["error"],
                        "content": str(result),
                    }
                )
            else:
                extracted_content.extend(result)

        return extracted_content

    def show_usage(self) -> None:
        """Print a detailed token usage report showing total and per-request usage."""
        print("\n=== Token Usage Summary ===")
        print(f"{'Type':<15} {'Count':>12}")
        print("-" * 30)
        print(f"{'Completion':<15} {self.total_usage.completion_tokens:>12,}")
        print(f"{'Prompt':<15} {self.total_usage.prompt_tokens:>12,}")
        print(f"{'Total':<15} {self.total_usage.total_tokens:>12,}")

        print("\n=== Usage History ===")
        print(f"{'Request #':<10} {'Completion':>12} {'Prompt':>12} {'Total':>12}")
        print("-" * 48)
        for i, usage in enumerate(self.usages, 1):
            print(
                f"{i:<10} {usage.completion_tokens:>12,} {usage.prompt_tokens:>12,} {usage.total_tokens:>12,}"
            )