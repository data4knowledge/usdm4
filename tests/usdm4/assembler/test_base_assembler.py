import os
import pathlib
import pytest
from simple_error_log.errors import Errors
from src.usdm4.assembler.base_assembler import BaseAssembler
from src.usdm4.builder.builder import Builder


def root_path():
    """Get the root path for the usdm4 package."""
    base = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
    return os.path.join(base, "src/usdm4")


@pytest.fixture(scope="module")
def builder():
    """Create a Builder instance for testing."""
    return Builder(root_path(), Errors())


@pytest.fixture(scope="module")
def errors():
    """Create an Errors instance for testing."""
    return Errors()


@pytest.fixture
def base_assembler(builder, errors):
    """Create a BaseAssembler instance for testing."""
    return BaseAssembler(builder, errors)


class TestBaseAssemblerInitialization:
    """Test BaseAssembler initialization."""

    def test_init_with_valid_parameters(self, builder, errors):
        """Test BaseAssembler initialization with valid parameters."""
        assembler = BaseAssembler(builder, errors)
        
        assert assembler._builder is builder
        assert assembler._errors is errors
        assert assembler.MODULE == "usdm4.assembler.base_assembler.BaseAssembler"

    def test_init_stores_builder_reference(self, builder, errors):
        """Test that BaseAssembler stores the builder reference correctly."""
        assembler = BaseAssembler(builder, errors)
        
        # Verify the builder reference is stored and accessible
        assert hasattr(assembler, '_builder')
        assert assembler._builder is builder
        assert isinstance(assembler._builder, Builder)

    def test_init_stores_errors_reference(self, builder, errors):
        """Test that BaseAssembler stores the errors reference correctly."""
        assembler = BaseAssembler(builder, errors)
        
        # Verify the errors reference is stored and accessible
        assert hasattr(assembler, '_errors')
        assert assembler._errors is errors
        assert isinstance(assembler._errors, Errors)

    def test_module_constant(self, base_assembler):
        """Test that the MODULE constant is set correctly."""
        assert hasattr(BaseAssembler, 'MODULE')
        assert BaseAssembler.MODULE == "usdm4.assembler.base_assembler.BaseAssembler"


