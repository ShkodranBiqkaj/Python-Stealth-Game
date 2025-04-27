import pytest
import pygame

class DummySurface:
    def get_width(self):
        return 40

    def get_height(self):
        return 40

    def convert_alpha(self):
        return self

# Stub functions instead of lambdas
def stub_load(path, *args, **kwargs):
    """Stub for pygame.image.load"""
    return DummySurface()

def stub_scale(surface, size, *args, **kwargs):
    """Stub for pygame.transform.scale"""
    # We ignore size and just return the passed-in dummy surface
    return surface

@pytest.fixture(autouse=True)
def dummy_pygame(monkeypatch):
    # Monkey-patch both image.load and transform.scale to our stubs
    monkeypatch.setattr(pygame.image, 'load', stub_load)
    monkeypatch.setattr(pygame.transform, 'scale', stub_scale)
    # No need to return anything; the patch is in effect for all tests