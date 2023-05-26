from ..base.curve import generate_call_wrapper as _wrapper

price, yields = _wrapper('price', 'yields')
prob, pd, marginal = _wrapper('prob', 'pd', 'marginal')
intensity, hazard_rate = _wrapper('intensity', 'hazard_rate')
df, rate, cash, short = _wrapper('df', 'rate', 'cash', 'short')
vol, instantaneous = _wrapper('vol', 'instantaneous')
