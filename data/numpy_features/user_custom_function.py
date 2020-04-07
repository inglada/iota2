def get_identity(self):
    # print("get identity")
    # print(self.get_B2())
    return self.get_Sentinel2_B2(), []


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
    import numpy as np
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
