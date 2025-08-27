from decimal import Decimal


def get_bmr_simple(pohlavi, vek, vyska, vaha):
    print("vykonavam funkci pro bmr")
    if pohlavi == "Muž":
        bmr = Decimal(88.362) + (Decimal(13.397)*vaha) + \
            (Decimal(4.799)*vyska) - (Decimal(5.677)*vek)
    else:
        bmr = Decimal(447.593) + (Decimal(9.247)*vaha) + \
            (Decimal(3.098)*vyska) - (Decimal(4.330)*vek)
    return float(bmr)


def get_bmr_advanced():
    pass


def get_tdee(bmr, vek, aktivita):
    print("vykonavam funkci pro tdee")
    if aktivita == "Sedavý":
        tdee = bmr*1.1
        return tdee

    if vek < 35:
        if aktivita == "Lehká aktivita":
            tdee = bmr*1.25
        elif aktivita == "Střední aktivita":
            tdee = bmr*1.35
        elif aktivita == "Vysoká aktivita":
            tdee = bmr*1.5
        else:
            tdee = bmr*1.7
    else:
        if aktivita == "Lehká aktivita":
            tdee = bmr*1.2
        elif aktivita == "Střední aktivita":
            tdee = bmr*1.3
        elif aktivita == "Vysoká aktivita":
            tdee = bmr*1.4
        else:
            tdee = bmr*1.5

    return tdee


def get_cals_cut(tdee, bmr, x):
    print("vykonavam funkci pro kalorie cut")
    deficit = (tdee-bmr)*x
    kalorie = tdee-deficit
    return kalorie


def get_cals_bulk(tdee, yes_count):
    print("vykonavam funkci pro kalorie bulk")
    if yes_count == 3:
        kalorie = tdee*1.2
    elif yes_count == 2:
        kalorie = tdee*1.15
    elif yes_count == 1:
        kalorie = tdee*1.1
    else:
        kalorie = tdee*1.05
    return kalorie


def get_macros_simple(cals, vaha):
    print("vykonavam funkci pro makra")
    denni_bilkoviny = int(round(vaha*2, 0))
    denni_tuky = int(round((cals*0.25)/9, 0))
    denni_sacharidy = int(
        round((cals - (denni_bilkoviny*4) - (denni_tuky*9))/4, 0))
    pitny_rezim = round((vaha*Decimal(37.5))/1000, 2)
    return denni_bilkoviny, denni_sacharidy, denni_tuky, pitny_rezim
