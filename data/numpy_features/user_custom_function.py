
def get_identity(self):
    print(self.get_band_b1())
    return self.get_band_b1()


def custom_function(self):
    print(dir(self))
    print(self.get_band_b1(), self.get_band_b2())
    return self.get_band_b1() + self.get_band_b2()


def custom_function_inv(self):
    print(dir(self))
    print(self.get_band_b1(), self.get_band_b2())
    return self.get_band_b1() - self.get_band_b2()
