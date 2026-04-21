from config.singleton import singleton


class TestSingleton:
    def test_returns_same_instance(self):
        @singleton
        class MyClass:
            def __init__(self, value):
                self.value = value

        a = MyClass(1)
        b = MyClass(2)
        assert a is b
        assert a.value == 1

    def test_different_classes_get_different_instances(self):
        @singleton
        class ClassA:
            pass

        @singleton
        class ClassB:
            pass

        assert ClassA() is not ClassB()

    def test_singleton_preserves_state(self):
        @singleton
        class Counter:
            def __init__(self):
                self.count = 0

        c1 = Counter()
        c1.count = 42
        c2 = Counter()
        assert c2.count == 42
