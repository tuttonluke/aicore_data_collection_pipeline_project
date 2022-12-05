#%%
from pandas.testing import assert_series_equal
from project_files.waterstones_query import QueryWaterstones
from unittest import TestCase
import pandas as pd
import unittest
#%%
class WaterstonesQueryTestCase(TestCase):
    """_summary_
    """
    @classmethod
    def setUpClass(cls) -> None:
        """Initiates an instance of the QueryWaterstones class before any 
        tests are run, loads the watersones.com homepage and accepts cookies.
        """
        cls.test_driver = QueryWaterstones()
        cls.test_driver.load_and_accept_cookies()

        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls) -> None:
        """Closes the browser once all tests are completed.
        """
        cls.test_driver.quit_browser()

        return super().tearDownClass()
    
    def setUp(self) -> None:
        """Generates a test driver object for each test.
        """
        self.test_driver.search("jose saramago")
        self.test_driver.get_language_filter_page_links()
        self.test_df = self.test_driver.get_DataFrame_of_language_filtered_query_results()

        return super().setUp()
    
    def test_dtypes(self):
        """_summary_
        """
        assert all(self.test_df.dtypes)
    
    def test_IDs(self):
        """_summary_
        """
        expected = pd.Series([9780099573586, 9782020403436, 9788490628720,
                        9788807721694, 9783442742868, 9789896602291
                        ]).astype(str).rename("ID")
        actual = self.test_df["ID"]
        assert_series_equal(expected, actual)


#%%
if __name__ == "__main__":
    unittest.main(argv=[''], exit=False)