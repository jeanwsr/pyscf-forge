import unittest
from pyscf import gto, scf, mp, df, dft
from pyscf.dh import RIEPAofDH
import numpy as np


def get_mf_h2o_hf():
    mol = gto.Mole(atom="O; H 1 0.94; H 1 0.94 2 104.5", basis="cc-pVTZ").build()
    return scf.RHF(mol).run()


def get_mf_hf_hf():
    # 10.1002/(SICI)1097-461X(2000)78:4<226::AID-QUA4>3.0.CO;2-N
    mol = gto.Mole()
    mol.atom = """
    H
    F 1 2.25
    """
    mol.basis = {
        "H": gto.basis.parse("""
            H S
             68.1600   0.00255
             10.2465   0.01938
              2.34648  0.09280
            H S
              0.673320 1.0
            H S
              0.224660 1.0
            H S
              0.082217 1.0
            H S
              0.043    1.0
            H P
              0.9      1.0
            H P
              0.3      1.0
            H P
              0.1      1.0
            H D
              0.8      1.0  
        """),
        "F": gto.basis.parse("""
            F S
              23340.    0.000757
               3431.    0.006081
                757.7   0.032636
                209.2   0.131704
                 66.73  0.396240
            F S
                 23.37  1.0
            F S
                  8.624 1.0
            F S
                  2.692 1.0
            F S
                  1.009 1.0
            F S
                  0.3312 1.0
            F P
                 65.66   0.037012
                 15.22   0.243943
                  4.788  0.808302
            F P
                  1.732  1.0
            F P
                  0.6206 1.0
            F P
                  0.2070 1.0
            F S
                  0.1000000              1.0000000        
            F P
                  0.0690000              1.0000000        
            F D
                  1.6400000              1.0000000        
            F D
                  0.5120000              1.0000000        
            F D
                  0.1600000              1.0000000        
            F D
                  0.0500000              1.0000000        
            F F
                  0.5000000              1.0000000
        """),
    }
    mol.build()
    mf_s = scf.RHF(mol).run()
    return mf_s


class TestEngRIEPA(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mf_h2o_hf = get_mf_h2o_hf()
        cls.mf_hf_hf = get_mf_hf_hf()

    def test_eng_riepa_conv_by_mp2(self):
        mf_s = self.mf_h2o_hf
        mf_dh = RIEPAofDH(mf_s)
        mf_dh.params.flags.update({
            "integral_scheme": "conv",
            "iepa_schemes": "MP2"
        })
        mf_dh.run()
        print(mf_dh.params.results)
        # reference value
        REF = -0.273944755130888
        REF_PYSCF = mp.MP2(mf_s).run().e_corr
        self.assertAlmostEqual(REF, REF_PYSCF, 8)
        self.assertAlmostEqual(mf_dh.params.results["eng_corr_MP2"], REF, 8)

    def test_eng_riepa_ri_by_mp2(self):
        mf_s = self.mf_h2o_hf
        mol = mf_s.mol
        mf_dh = RIEPAofDH(mf_s)
        mf_dh.params.flags.update({"iepa_schemes": "MP2"})
        mf_dh.run()
        print(mf_dh.params.results)
        # reference value
        REF = -0.2739374133400274
        mf_s.with_df = df.DF(mol, auxbasis=df.aug_etb(mol))
        REF_PYSCF = mp.dfmp2.DFMP2(mf_s).run().e_corr
        print(REF_PYSCF)
        self.assertAlmostEqual(REF, REF_PYSCF, 8)
        self.assertAlmostEqual(mf_dh.params.results["eng_corr_MP2"], REF, 8)

    def test_eng_rmp2cr_conv(self):
        mf_s = self.mf_hf_hf
        mf_dh = RIEPAofDH(mf_s)
        mf_dh.params.flags.update({
            "integral_scheme": "conv",
            "iepa_schemes": ["MP2", "MP2cr", "MP2cr2"]
        })
        mf_dh.run()
        print(mf_dh.params.results)
        # reference value from 10.1002/(SICI)1097-461X(2000)78:4<226::AID-QUA4>3.0.CO;2-N
        KNOWN_MP2 = -0.3523338
        KNOWN_MP2CR1 = -0.3362996
        KNOWN_MP2CR2 = -0.3250326
        KNOWN_MP2CR3 = -0.3443167
        KNOWN_MP2CR4 = -0.3386832
        eng_corr_MP2 = mf_dh.params.results["eng_corr_MP2"]
        eng_corr_MP2CR = mf_dh.params.results["eng_corr_MP2CR"]
        eng_corr_MP2CR2 = mf_dh.params.results["eng_corr_MP2CR2"]
        DELTA = 1e-5
        self.assertAlmostEqual(eng_corr_MP2, KNOWN_MP2, delta=DELTA)
        self.assertAlmostEqual(eng_corr_MP2CR, KNOWN_MP2CR1, delta=DELTA)
        self.assertAlmostEqual(eng_corr_MP2CR2, KNOWN_MP2CR2, delta=DELTA)
        self.assertAlmostEqual(0.5 * (eng_corr_MP2 + eng_corr_MP2CR), KNOWN_MP2CR3, delta=DELTA)
        self.assertAlmostEqual(0.5 * (eng_corr_MP2 + eng_corr_MP2CR2), KNOWN_MP2CR4, delta=DELTA)

    def test_eng_rmp2cr_converge(self):
        # coverage only, not testing correctness
        mf_s = self.mf_h2o_hf

        mf_dh = RIEPAofDH(mf_s)
        mf_dh.params.flags.update({
            "iepa_schemes": ["MP2", "MP2cr", "MP2cr2", "IEPA", "sIEPA", "DCPT2"],
            "omega_list_iepa": [0, 0.7, -0.7],
        })
        mf_dh.run().run()

        eri = mf_s._eri.copy()
        mf_s._eri = None

        mf_dh = RIEPAofDH(mf_s)
        mf_dh.params.flags.update({
            "integral_scheme_iepa": "conv",
            "iepa_schemes": ["MP2cr", "IEPA", "sIEPA"],
        })
        mf_dh.run()

        with self.assertRaises(ValueError):
            mf_dh.params.flags.update({"iepa_schemes": ["RPA"]})
            mf_dh.run()

        mf_s._eri = eri
