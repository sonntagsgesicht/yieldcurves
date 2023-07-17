
from test.unittests._analytics_wrapper_tests import IdentityUnitTests, Prob, \
    Marginal, ProbM, lin, ascii_plot, Intensity, Cash, ZeroC, Cv

self = IdentityUnitTests()
self.setUp()
curve = 0.2
origin = Cv(curve)
transform = ZeroC(Cash(origin, frequency=4), frequency=4)
# origin = Intensity(origin)
x = 2.41
a = transform(x)
b = origin(x)
print(a, b, a - b)
# exit()


X = lin(0, 7, 0.1)
t = lambda x: transform(x) - origin(x)
ascii_plot(X, origin, transform)
ascii_plot(X, t)
for x in X:
    print(x, t(x))
    pass
