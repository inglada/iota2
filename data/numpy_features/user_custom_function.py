import numpy as np


# ############################################################################
# S2 tests utilities functions
# ############################################################################
def get_identity(self):
    # print("get identity")
    # print(self.get_B2())

    return self.get_Sentinel2_B2(), []


def test_index_sum(self):
    coef = self.get_Sentinel2_B2() + self.get_Sentinel2_B4()
    labels = []
    return np.sum(coef, axis=2), labels


def test_index(self):
    coef = self.get_Sentinel2_B2() + self.get_Sentinel2_B4()
    labels = []
    return coef, labels


def duplicate_ndvi(self):
    ndvi = self.get_Sentinel2_NDVI()
    labels = [f"dupndvi_{i+1}" for i in range(ndvi.shape[2])]
    return ndvi, labels


def get_ndvi(self):
    coef = (self.get_Sentinel2_B8() - self.get_Sentinel2_B4()) / (
        self.get_Sentinel2_B4() + self.get_Sentinel2_B8())
    labels = [f"ndvi_{i+1}" for i in range(coef.shape[2])]
    return coef, labels


def custom_function(self):
    print(dir(self))
    print(self.get_Sentinel2_b1(), self.get_Sentinel2_b2())
    return self.get_Sentinel2_b1() + self.get_Sentinel2_b2()


def custom_function_inv(self):
    print(dir(self))
    print(self.get_Sentinel2_b1(), self.get_Sentinel2_b2())
    return self.get_Sentinel2_b1() - self.get_Sentinel2_b2()


def get_ndsi(self):
    coef = (self.get_Sentinel2_B3() - self.get_Sentinel2_B11()) / (
        self.get_Sentinel2_B3() + self.get_Sentinel2_B11())
    labels = [f"ndsi_{i+1}" for i in range(coef.shape[2])]
    print("out custom features")
    return coef, labels


def get_cari(self):
    a = ((self.get_Sentinel2_B5() - self.get_Sentinel2_B3()) /
         150) * 670 + self.get_Sentinel2_B4() + (self.get_Sentinel2_B3() - (
             (self.get_Sentinel2_B5() - self.get_Sentinel2_B3()) / 150) * 550)
    b = ((self.get_Sentinel2_B5() - self.get_Sentinel2_B3()) / (150 * 150)) + 1
    coef = (self.get_Sentinel2_B5() / self.get_Sentinel2_B4()) * (
        (np.sqrt(a * a)) / (np.sqrt(b)))
    labels = [f"cari_{i+1}" for i in range(coef.shape[2])]

    return coef, labels


def get_red_edge2(self):
    coef = (self.get_Sentinel2_B5() - self.get_Sentinel2_B4()) / (
        self.get_Sentinel2_B5() + self.get_Sentinel2_B4())
    labels = [f"rededge2_{i+1}" for i in range(coef.shape[2])]
    return coef, labels


def get_gndvi(self):
    """
        compute the Green Normalized Difference Vegetation Index
        DO NOT USE this except for test as Sentinel2 has not B9
    """
    coef = (self.get_Sentinel2_B9() - self.get_Sentinel2_B3()) / (
        self.get_Sentinel2_B9() + self.get_Sentinel2_B3())
    labels = [f"gndvi_{i+1}" for i in range(coef.shape[2])]
    return coef, labels


def get_soi(self):
    """
       compute the Soil Composition Index
    """
    coef = (self.get_Sentinel2_B11() - self.get_Sentinel2_B8()) / (
        self.get_Sentinel2_B11() + self.get_Sentinel2_B8())
    labels = [f"soi_{i+1}" for i in range(coef.shape[2])]
    return coef, labels


# ############################################################################
# DHI INDEX
# ############################################################################


def get_cumulative_productivity(self):
    print("cumul")
    coef = np.sum(self.get_Sentinel2_NDVI(), axis=2)
    labels = ["cumul_prod"]
    return coef, labels


def get_minimum_productivity(self):
    print("min")
    coef = np.min(self.get_Sentinel2_NDVI(), axis=2)
    labels = ["min_prod"]
    return coef, labels


def get_seasonal_variation(self):
    print("var")
    coef = (np.std(self.get_Sentinel2_NDVI(), axis=2) /
            (np.mean(self.get_Sentinel2_NDVI(), axis=2) + 1E-6))

    labels = ["var_prod"]
    return coef, labels


# ###########################################################################
# Functions for testing all sensors
# ###########################################################################


def test_index_sum_l5_old(self):
    coef = self.get_Landsat5Old_B2() + self.get_Landsat5Old_B4()
    labels = []
    return np.sum(coef, axis=2), labels


def test_index_l5_old(self):
    coef = self.get_Landsat5Old_B2() + self.get_Landsat5Old_B4()
    labels = []
    return coef, labels


def test_index_sum_l8_old(self):
    coef = self.get_Landsat8Old_B2() + self.get_Landsat8Old_B4()
    labels = []
    return np.sum(coef, axis=2), labels


def test_index_l8_old(self):
    coef = self.get_Landsat8Old_B2() + self.get_Landsat8Old_B4()
    labels = []
    return coef, labels


def test_index_sum_l8(self):
    coef = self.get_Landsat8_B2() + self.get_Landsat8_B4()
    labels = []
    return np.sum(coef, axis=2), labels


def test_index_l8(self):
    coef = self.get_Landsat8_B2() + self.get_Landsat8_B4()
    labels = []
    return coef, labels


def test_index_sum_s2_s2c(self):
    coef = self.get_Sentinel2S2C_B02() + self.get_Sentinel2S2C_B04()
    labels = []
    return np.sum(coef, axis=2), labels


def test_index_s2_s2c(self):
    coef = self.get_Sentinel2S2C_B02() + self.get_Sentinel2S2C_B04()
    labels = []
    return coef, labels


def test_index_sum_s2_l3a(self):
    coef = self.get_Sentinel2L3A_B2() + self.get_Sentinel2L3A_B4()
    labels = []
    return np.sum(coef, axis=2), labels


def test_index_s2_l3a(self):
    coef = self.get_Sentinel2L3A_B2() + self.get_Sentinel2L3A_B4()
    labels = []
    return coef, labels
