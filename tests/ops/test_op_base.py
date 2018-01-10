from trane.ops.op_base import OpBase
from trane.utils.table_meta import TableMeta as TM
import pytest

class FakeOp(OpBase):
    """
    Make a fake operation for testing. 
    It has PARAMS and IOTYPES, but execute is not implemented
    """
    PARAMS = [{'param': TM.TYPE_VALUE}, {'param': TM.TYPE_TEXT}]
    IOTYPES = [(TM.TYPE_VALUE, TM.TYPE_BOOL), (TM.TYPE_TEXT, TM.TYPE_BOOL)]

def test_op_base_init():
    """
    Check if FakeOp is initialized correctly.
    Check if NotImplementedError is raised.
    """
    op = FakeOp('col')
    assert op.itype is None
    assert op.otype is None
    assert type(op.param_values) == dict
    with pytest.raises(NotImplementedError):
        op(None)

def test_preprocess_with_correct_type1():
    """
    With input type TYPE_VALUE, check if itype and otype are correct.
    """
    meta = TM([{'name': 'col', 'type': TM.TYPE_VALUE}])
    op = FakeOp('col')
    meta2 = op.preprocess(meta)
    assert meta2 == meta
    assert meta.get_type('col') == TM.TYPE_BOOL
    assert op.itype == TM.TYPE_VALUE and op.otype == TM.TYPE_BOOL

def test_preprocess_with_correct_type2():    
    """
    With input type TYPE_TEXT, check if itype and otype are correct.
    """
    meta = TM([{'name': 'col', 'type': TM.TYPE_TEXT}])
    op = FakeOp('col')
    meta2 = op.preprocess(meta)
    assert meta2 == meta
    assert meta.get_type('col') == TM.TYPE_BOOL
    assert op.itype == TM.TYPE_TEXT and op.otype == TM.TYPE_BOOL    
    
def test_preprocess_with_wrong_type():
    """
    with input type TYPE_IDENTIFIER, check if None is returned by preprocess.
    """
    meta = TM([{'name': 'col', 'type': TM.TYPE_IDENTIFIER}])
    op = FakeOp('col')
    meta2 = op.preprocess(meta)
    assert meta2 is None
    assert meta.get_type('col') == TM.TYPE_IDENTIFIER
    assert op.itype is TM.TYPE_IDENTIFIER and op.otype is None
    
