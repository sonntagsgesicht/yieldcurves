from .adapter import PriceAdapter, ForeignExchangeRateAdapter, \
    InterestRateAdapter, CreditAdapter, VolatilityAdapter


# --- PriceOperators ---


class PriceOperator(PriceAdapter):
    """PriceAdapter -> PriceAdapter"""

    def price(self, x, y=None):
        return self.curve.price(x, y)

    def price_yield(self, x, y=None):
        return self.curve.price_yield(x, y)


class Price(PriceAdapter):
    """PriceAdapter -> Price"""

    def __init__(self, curve: PriceAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.price(x, y)


class PriceYield(PriceAdapter):
    """PriceAdapter -> PriceYield"""

    def __init__(self, curve: PriceAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.price_yield(x, y)


# --- FxRateOperators ---


class Fx(ForeignExchangeRateAdapter):
    """AssetPriceYield/InterestRateAdapter -> FxRate"""

    def __call__(self, x, y=None):
        return self.fx(x, y)

    def fx(self, x, y=None):
        return self.curve.fx(x, y)


# --- InterestRateOperators ---


class InterestRateOperator(InterestRateAdapter):
    """InterestRateAdapter -> InterestRateAdapter"""

    def zero(self, x, y=None):
        return self.curve.zero(x, y)

    def df(self, x, y=None):
        return self.curve.df(x, y)

    def short(self, x, y=None):
        return self.curve.short(x, y)


class Zero(InterestRateOperator):
    """InterestRateAdapter -> ZeroRate"""

    def __init__(self, curve: InterestRateAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.zero(x, y)


class Df(InterestRateOperator):
    """InterestRateAdapter -> DiscountFactor"""

    def __init__(self, curve: InterestRateAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.df(x, y)


class Short(InterestRateOperator):
    """InterestRateAdapter -> ShortRate"""

    def __init__(self, curve: InterestRateAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.short(x, y)


class Cash(InterestRateOperator):
    """InterestRateAdapter -> CashRate"""

    def __init__(self, curve: InterestRateAdapter, cash_frequency=None):
        super().__init__(curve, cash_frequency=cash_frequency)

    def __call__(self, x, y=None):
        return self.cash(x, y)


class Par(InterestRateOperator):
    """InterestRateAdapter -> SwapParRate"""

    def __init__(self, curve: InterestRateAdapter,
                 cash_frequency=None, forward_curve=None):
        super().__init__(curve, cash_frequency=cash_frequency,
                         forward_curve=forward_curve)

    def __call__(self, x, y=None):
        return self.par(x, y)


class Annuity(InterestRateOperator):
    """InterestRateAdapter -> SwapAnnuityRate"""

    def __init__(self, curve: InterestRateAdapter, cash_frequency=None):
        super().__init__(curve, cash_frequency=cash_frequency)

    def __call__(self, x, y=None):
        return self.annuity(x, y)


# --- CreditOperators ---


class CreditOperator(CreditAdapter):
    """CreditAdapter -> CreditAdapter"""

    def prob(self, x, y=None):
        return self.curve.prob(x, y)

    def intensity(self, x, y=None):
        return self.curve.intensity(x, y)

    def hz(self, x, y=None):
        return self.curve.hz(x, y)

    def marginal(self, x, y=None):
        return self.curve.marginal(x, y)

    def pd(self, x, y=None):
        return self.curve.pd(x, y)


class Prob(CreditOperator):
    """CreditAdapter -> SurvivalProbability"""

    def __init__(self, curve: CreditAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.prob(x, y)


class Intensity(CreditAdapter):
    """CreditAdapter -> FlatIntensity"""

    def __init__(self, curve: CreditAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.intensity(x, y)


class Hz(CreditAdapter):
    """CreditAdapter -> HazardRate"""

    def __init__(self, curve: CreditAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.hz(x, y)


class Marginal(CreditAdapter):
    """CreditAdapter -> MarginalSurvivalProbability"""

    def __init__(self, curve: CreditAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.marginal(x, y)


class Pd(CreditAdapter):
    """CreditAdapter -> DefaultProbability"""

    def __init__(self, curve: CreditAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.pd(x, y)


# --- VolatilityOperators ---


class VolatilityOperator(VolatilityAdapter):
    """VolatilityAdapter -> VolatilityAdapter"""

    def vol(self, x, y=None):
        return self.curve.vol(x, y)

    def terminal(self, x, y=None):
        return self.curve.terminal(x, y)


class Vol(VolatilityOperator):
    """VolatilityAdapter -> InstantaneousVol"""

    def __init__(self, curve: VolatilityAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.vol(x, y)


class Terminal(VolatilityOperator):
    """VolatilityAdapter -> TerminalVol"""

    def __init__(self, curve: VolatilityAdapter):
        super().__init__(curve)

    def __call__(self, x, y=None):
        return self.terminal(x, y)

