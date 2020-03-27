def get_identity(self):
    # print("get identity")
    # print(self.get_band_B2())
    return self.get_Sentinel2_band_B2(), []


def get_ndvi(self):
    coef = (self.get_Sentinel2_band_B8() - self.get_Sentinel2_band_B4()) / (
        self.get_Sentinel2_band_B4() + self.get_Sentinel2_band_B8())
    labels = [f"ndvi_{i+1}" for i in range(coef.shape[2])]
    return coef, labels


def custom_function(self):
    print(dir(self))
    print(self.get_Sentinel2_band_b1(), self.get_Sentinel2_band_b2())
    return self.get_Sentinel2_band_b1() + self.get_Sentinel2_band_b2()


def custom_function_inv(self):
    print(dir(self))
    print(self.get_Sentinel2_band_b1(), self.get_Sentinel2_band_b2())
    return self.get_Sentinel2_band_b1() - self.get_Sentinel2_band_b2()


def get_ndsi(self):
    coef = (self.get_Sentinel2_band_B3() - self.get_Sentinel2_band_B11()) / (
        self.get_Sentinel2_band_B3() + self.get_Sentinel2_band_B11())
    labels = [f"ndsi_{i+1}" for i in range(coef.shape[2])]
    print("out custom features")
    return coef, labels


def get_cari(self):
    import numpy as np
    a = (
        (self.get_Sentinel2_band_B5() - self.get_Sentinel2_band_B3()) / 150
    ) * 670 + self.get_Sentinel2_band_B4() + (self.get_Sentinel2_band_B3() - (
        (self.get_Sentinel2_band_B5() - self.get_Sentinel2_band_B3()) / 150) *
                                              550)
    b = ((self.get_Sentinel2_band_B5() - self.get_Sentinel2_band_B3()) /
         (150 * 150)) + 1
    coef = (self.get_Sentinel2_band_B5() / self.get_Sentinel2_band_B4()) * (
        (np.sqrt(a * a)) / (np.sqrt(b)))
    labels = [f"cari_{i+1}" for i in range(coef.shape[2])]

    return coef, labels
