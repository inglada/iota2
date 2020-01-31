
def get_identity(self):
    print(self.get_band_B2())
    return self.get_band_B2()


def get_ndvi(self):
    coef = ((self.get_band_B8() - self.get_band_B4()) /
            (self.get_band_B4() + self.get_band_B8()))
    return coef


def custom_function(self):
    print(dir(self))
    print(self.get_band_b1(), self.get_band_b2())
    return self.get_band_b1() + self.get_band_b2()


def custom_function_inv(self):
    print(dir(self))
    print(self.get_band_b1(), self.get_band_b2())
    return self.get_band_b1() - self.get_band_b2()
