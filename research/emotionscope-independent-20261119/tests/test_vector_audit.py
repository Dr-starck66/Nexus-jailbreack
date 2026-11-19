"""Test the independent format reader; synthetic files are not real-model evidence."""
import io
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_vector_checkpoint import (
    geometry_report, RestrictedCheckpointUnpickler, parse_checkpoint,
    rebuild_tensor, Storage, norm, cos)
import torch
class VectorAuditTests(unittest.TestCase):
    def test_safe_format(self):
        names=('happy','sad','afraid','angry','calm','desperate','hopeful','frustrated','curious','proud','guilty','surprised','loving','hostile','nervous','confident','brooding','enthusiastic','reflective','gloomy')
        torch.manual_seed(1)
        vecs={n:torch.nn.functional.normalize(torch.randn(2304),dim=0) for n in names}
        data={'vectors':vecs,'raw_vectors':vecs,'neutral_pca':torch.randn(2304,19),
              'model_info':{'model_name':'google/gemma-2-2b-it','d_model':2304,'probe_layer':22,'n_layers':26,'backend':'transformer_lens'},
              'probe_layer_used':22,'emotions':[{'name':n} for n in names]}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'synthetic.pt'
            torch.save(data,p)
            saved,vectors,digest,size=parse_checkpoint(p,expected_sha256='')
            self.assertEqual(len(vectors),20)
            self.assertEqual(size,p.stat().st_size)
            report=geometry_report(p,expected_sha256='')
            self.assertEqual(report['n_vectors'],20)
            self.assertLess(abs(report['min_l2_norm']-1),0.00001)
    def test_forbid_arbitrary_global(self):
        import pickle
        with self.assertRaises(pickle.UnpicklingError):
            RestrictedCheckpointUnpickler(io.BytesIO(pickle.dumps(complex(1,2)))).load()
    def test_stride_rejection(self):
        with self.assertRaises(ValueError):
            rebuild_tensor(Storage('0',10),0,(10,),(2,),False,{})
    def test_metrics(self):
        self.assertAlmostEqual(norm([3.,4.]),5.)
        self.assertAlmostEqual(cos([1.,0.],[0.,1.]),0.)
        self.assertAlmostEqual(cos([1.,0.],[1.,0.]),1.)
if __name__=='__main__':unittest.main()
