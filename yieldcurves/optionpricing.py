# -*- coding: utf-8 -*-
# dcf
# ---
# A Python library for generating discounted cashflows.
#
# Author:   sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]
# Version:  0.7, copyright Sunday, 22 May 2022
# Website:  https://github.com/sonntagsgesicht/dcf
# License:  Apache License 2.0 (see LICENSE file)

from math import exp, log, sqrt

from prettyclass import prettyclass


r""" The pre-factor of the normal density: $1/\sqrt{2\Pi}$. """
_ONE_OVER_SQRT_OF_TWO_PI = 0.398942280401433


def _normal_pdf(x):
    """ Density function for normal distribution
    @param x: float value
    @return value of normal density function
    """
    return _ONE_OVER_SQRT_OF_TWO_PI * exp(-0.5 * x * x)


def _normal_cdf(x):
    """
    The cumulative distribution function of the standard normal distribution.
    The standard implementation, following Abramowitz/Stegun, (26.2.17).
    """
    if x >= 0:
        # if x > 7.0:
        #    return 1 - _ONE_OVER_SQRT_OF_TWO_PI * exp(-0.5*x*x)/sqrt(1.0+x*x)
        result = 1.0 / (1.0 + 0.2316419 * x)
        ret = 1.0 - _ONE_OVER_SQRT_OF_TWO_PI * exp(-0.5 * x * x) * (
            result * (0.31938153 +
                      result * (-0.356563782 +
                                result * (1.781477937 +
                                          result * (-1.821255978 +
                                                    result * 1.330274429)))))
        return ret

    else:
        # if x < -7.0:
        #    return 1 - one_over_sqrt_of_two_pi() * exp(-0.5*x*x)/sqrt(1.0+x*x)
        result = 1.0 / (1.0 - 0.2316419 * x)
        ret = _ONE_OVER_SQRT_OF_TWO_PI * exp(-0.5 * x * x) * (
            result * (0.31938153 +
                      result * (-0.356563782 +
                                result * (1.781477937 +
                                          result * (-1.821255978 +
                                                    result * 1.330274429)))))

        return ret


@prettyclass(init=False)
class OptionPricingFormula:
    r"""abstract base class for option pricing formulas

    A |OptionPricingFormula()| $f$ serves as a kind of supply template
    to enhance |OptionPricingCurve()| by a new methodology.

    To do so, $f$ should at least implement a method
    **__call__(time, strike, forward, volatility)**
    to provide the expected payoff of an European call option.

    These and all following method are only related to call options
    since put options will be derived by the use of
    `put-call parity <https://en.wikipedia.org/wiki/Put–call_parity>`_.

    Moreover, the **volatility** argument should be understood as
    a general input of model parameters which ar in case of classical
    option pricing formulas like |Black76()|
    the volatility.

    To provide non-numerical derivatives implement

    delta $\Delta_f$, the first derivative along the underlying

    gamma $\Gamma_f$, the second derivative along the underlying

    vega $\mathcal{V}_f$, the first derivative along the volatility parameters

    theta $\Theta_f$, the first derivative along the time parameter **time**

    Moreover, similar methods for binary options may be provided.

    """

    # --- vanilla

    def __call__(self, time, strike, forward, volatility):
        return 0.0

    def delta(self, time, strike, forward, volatility):
        return

    def gamma(self, time, strike, forward, volatility):
        return

    def vega(self, time, strike, forward, volatility):
        return

    def theta(self, time, strike, forward, volatility):
        return

    # --- binary

    def binary(self, time, strike, forward, volatility):
        return

    def binary_delta(self, time, strike, forward, volatility):
        return

    def binary_gamma(self, time, strike, forward, volatility):
        return

    def binary_vega(self, time, strike, forward, volatility):
        return

    def binary_theta(self, time, strike, forward, volatility):
        return


class Intrinsic(OptionPricingFormula):
    r""" intrisic option pricing formula

    implemented for call options
    (`see more on intrisic option values
    <https://en.wikipedia.org/wiki/Option_time_value>`_)

    Let $F$ be the current forward value.
    Let $K$ be the option strike value,
    $\tau$ the time to matruity, i.e. the option expitry date.

    Then

        * call price: $$\max(F-K, 0)$$

        * call delta: $$0 \text{ if } F < K \text{ else } 1$$

        * call gamma: $$0$$

        * call vega: $$0$$

        * binary call price: $$0 \text{ if } F < K \text{ else } 1$$

        * binary call delta: $$0$$

        * binary call gamma: $$0$$

        * binary call vega: $$0$$

    """

    # --- vanilla

    def __call__(self, time, strike, forward, volatility):
        return max(forward - strike, 0.0)

    def delta(self, time, strike, forward, volatility):
        return 0.0 if forward < strike else 1.0

    def gamma(self, time, strike, forward, volatility):
        return 0.0

    def vega(self, time, strike, forward, volatility):
        return 0.0

    def theta(self, time, strike, forward, volatility):
        return 0.0

    # --- binary

    def binary(self, time, strike, forward, volatility):
        return 0.0 if forward <= strike else 1.0

    def binary_delta(self, time, strike, forward, volatility):
        return 0.0

    def binary_gamma(self, time, strike, forward, volatility):
        return 0.0

    def binary_vega(self, time, strike, forward, volatility):
        return 0.0

    def binary_theta(self, time, strike, forward, volatility):
        return 0.0


class Bachelier(OptionPricingFormula):
    r""" Bachelier option pricing formula

    implemented for call options
    (`see more on Bacheliers model
    <https://en.wikipedia.org/wiki/Bachelier_model>`_)

    Let $f$ be a normaly distributed random variable
    with expectation $F=E[f]$, the current forward value
    and $\Phi$ the standard normal cummulative distribution function
    s.th. $\phi=\Phi'$ is its density function.

    Let $K$ be the option strike value,
    $\tau$ the time to matruity, i.e. the option expitry date, and
    $\sigma$ the volatility parameter,
    i.e. the standard deviation of $f$.
    Moreover, let $$d = \frac{F-K}{\sigma \cdot \sqrt{\tau}}$$

    Then

        * call price:
          $$(F-K) \cdot \Phi(d) + \sigma \cdot \sqrt{\tau} \cdot \phi(d)$$

        * call delta: $$\Phi(d)$$

        * call gamma: $$\frac{\phi(d)}{\sigma \cdot \sqrt{\tau}}$$

        * call vega: $$\sqrt{\tau} \cdot \phi(d)$$

        * binary call price: $$\Phi(d)$$

        * binary call delta: $$\frac{\phi(d)}{\sigma \cdot \sqrt{\tau}}$$

        * binary call gamma: $$d \cdot \frac{\phi(d)}{\sigma^2 \cdot \tau}$$

        * binary call vega: $$\sqrt{\tau} \cdot \phi(d)$$

    """

    # --- vanilla

    def __call__(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return (forward - strike) * _normal_cdf(d) + vol * _normal_pdf(d)

    def delta(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return _normal_cdf(d)

    def gamma(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return _normal_pdf(d) / vol

    def vega(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return sqrt(time) * _normal_pdf(d)

    # --- binary

    def binary(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return _normal_cdf(d)

    def binary_delta(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return _normal_pdf(d) / vol

    def binary_gamma(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return d * _normal_pdf(d) / (vol * vol * time)

    def binary_vega(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (forward - strike) / vol
        return sqrt(time) * _normal_pdf(d)


class Black76(OptionPricingFormula):
    r""" Black 76 option pricing formula

    implemented for call options
    (`see more on Black 76 model
    <https://en.wikipedia.org/wiki/Black_model>`_
    which is closly related to the
    `Black-Scholes model
    <https://en.wikipedia.org/wiki/Black–Scholes_model>`_)

    Let $f$ be a log-normaly distributed random variable
    with expectation $F=E[f]$, the current forward value
    and $\Phi$ the standard normal cummulative distribution function
    s.th. $\phi=\Phi'$ is its density function.

    Let $K$ be the option strike value,
    $\tau$ the time to maturity, i.e. the option expiry date, and
    $\sigma$ the volatility parameter,
    i.e. the standard deviation of $\log(f)$.
    Moreover, let
    $$d =\frac{\log(F/K) + (\sigma^2 \cdot \tau)/2}{\sigma \cdot \sqrt{\tau}}$$

    Then

        * call price:
          $$F \cdot \Phi(d) - K \cdot \Phi(d-\sigma \cdot \sqrt{\tau})$$

        * call delta: $$\Phi(d)$$

        * call gamma: $$\frac{\phi(d)}{F \cdot \sigma \cdot \sqrt{\tau}}$$

        * call vega: $$F \cdot \sqrt{\tau} \cdot \phi(d)$$

        * binary call price: $$\Phi(d)$$

        * binary call delta:
          $$\frac{\phi(d-\sigma \cdot \sqrt{\tau})}{\sigma \cdot \sqrt{\tau}}$$

        * binary call gamma: $$d \cdot \frac{\phi(d)}{\sigma^2 \cdot \tau}$$

        * binary call vega: $$(d/\sigma - \sqrt{\tau}) \cdot \phi(d)$$

    """

    # --- vanilla

    def __call__(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return forward * _normal_cdf(d) - strike * _normal_cdf(d - vol)

    def delta(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return _normal_cdf(d)

    def gamma(self, time, strike, forward, volatility):
        # vol = volatility * sqrt(time)
        # d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return  # TODO Black76 gamma

    def vega(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return forward * sqrt(time) * _normal_pdf(d - vol)

    # --- binary

    def binary(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return _normal_cdf(d)

    def binary_delta(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return _normal_pdf(d - vol) / (vol * forward)

    def binary_gamma(self, time, strike, forward, volatility):
        # vol = volatility * sqrt(time)
        # d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return  # TODO Black76 gamma for digital payoff

    def binary_vega(self, time, strike, forward, volatility):
        vol = volatility * sqrt(time)
        d = (log(forward / strike) + (vol ** 2 / 2)) / vol
        return (d - vol) * _normal_pdf(d) / volatility


class DisplacedBlack76(OptionPricingFormula):
    r""" displaced Black 76 option pricing formula

    implemented for call options
    (see also |Black76()|)

    The displaced Black 76 is adopted to handel moderate negative
    underlying forward prices or rates $f$,
    e.g. as see for interest rates in the past.
    To do so, rather than $f$ a shifted or displaced version $f + \alpha$
    is assumed to be log-normally distributed
    for some negative value of $\alpha$.

    Hence, let $f + \alpha$ be a log-normally distributed random variable
    with expectation $F + \alpha=E[f + \alpha]$,
    where $F=E[f]$ is the current forward value
    and $\Phi$ the standard normal cumulative distribution function
    s.th. $\phi=\Phi'$ is its density function.

    Uses |Black76()| formulas
    with

        * displaced forward $F+\alpha$

    and

        * displaced strike $K+\alpha$

    Let $K$ be the option strike value,
    $\tau$ the time to maturity, i.e. the option expiry date, and
    $\sigma$ the volatility parameter,
    i.e. the standard deviation of $\log(f + \alpha)$.
    Moreover, let
    $$d =\frac{\log((F+\alpha)/(K+\alpha))
    + (\sigma^2 \cdot \tau)/2}{\sigma \cdot \sqrt{\tau}}$$

    Then

        * call price:
          $$(F+\alpha) \cdot \Phi(d)
          - (K+\alpha) \cdot \Phi(d-\sigma \cdot \sqrt{\tau})$$

        * call delta: $$\Phi(d)$$

        * call gamma:
          $$\frac{\phi(d)}{(F+\alpha) \cdot \sigma \cdot \sqrt{\tau}}$$

        * call vega: $$(F+\alpha) \cdot \sqrt{\tau} \cdot \phi(d)$$

        * binary call price:

        * binary call delta:

        * binary call gamma:

        * binary call vega:

    """

    INNER = Black76()

    def __init__(self, displacement=0.0):
        self.displacement = displacement

    def __call__(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self.INNER(time, strike, forward, volatility)

    def delta(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self.INNER.delta(time, strike, forward, volatility)

    def gamma(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self.INNER.gamma(time, strike, forward, volatility)

    def vega(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self.INNER.vega(time, strike, forward, volatility)

    def theta(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self.INNER.theta(time, strike, forward, volatility)

    # --- binary

    def binary(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self.INNER.binary(time, strike, forward, volatility)

    def binary_delta(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self.INNER.binary_delta(time, strike, forward, volatility)

    def binary_gamma(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self.INNER.binary_gamma(time, strike, forward, volatility)

    def binary_vega(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self.INNER.binary_vega(time, strike, forward, volatility)

    def binary_theta(self, time, strike, forward, volatility):
        strike += self.displacement
        forward += self.displacement
        return self.INNER.binary_theta(time, strike, forward, volatility)
