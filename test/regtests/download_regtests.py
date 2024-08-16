from regtest import RegressionTestCase

from yieldcurves.models.nelsonsiegel import download_ecb, \
    NelsonSiegelSvensson as NSS


class DownloadRegTests(RegressionTestCase):

    def test_download_ecb(self):
        dl = download_ecb()
        self.assertRegressiveEqual(1 == len(dl))
        dl = download_ecb(start='2020-01-01', end='2020-03-31')
        self.assertRegressiveEqual(dl)
        # dl2 = download_ecb(start=20200101, end=20200331)
        # self.assertRegressiveEqual(dl == dl2)

    def test_download_nss(self):
        NSS._download = {}
        self.assertRegressiveEqual(0 == len(NSS._download))
        NSS.download()
        self.assertRegressiveEqual(10 == len(NSS._download))
        self.assertRegressiveEqual(
            len(NSS.download_dates) == len(NSS._download))
        date = '2020-02-24'
        NSS.download(date)
        self.assertRegressiveEqual(11 < len(NSS._download))
        self.assertRegressiveEqual(NSS.download_dates[0] == date)
