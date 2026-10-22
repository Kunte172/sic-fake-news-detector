Training logistic_regression...
Training multinomial_nb...
Training linear_svm...
{
  "experiment": "ml-01-audited-classic-models-v1",
  "input_sha256": "05d9736daedb95cd97732f0d0368937b4ba424ebb1f88031f72d8c127f4c1760",
  "label_map": {
    "0": "Fake",
    "1": "Real"
  },
  "feature": "text_clean",
  "split_counts": {
    "train": 30537,
    "validation": 3824,
    "test": 3803
  },
  "selection": "highest validation macro F1; Fake F1 breaks ties",
  "selected_model": "linear_svm",
  "results": {
    "logistic_regression": {
      "validation": {
        "articles": 3824,
        "accuracy": 0.983787,
        "f1_fake": 0.981559,
        "f1_macro": 0.983546,
        "confusion_matrix_rows_fake_real": [
          [
            1650,
            48
          ],
          [
            14,
            2112
          ]
        ]
      },
      "test": {
        "articles": 3803,
        "accuracy": 0.982908,
        "f1_fake": 0.980706,
        "f1_macro": 0.982683,
        "confusion_matrix_rows_fake_real": [
          [
            1652,
            40
          ],
          [
            25,
            2086
          ]
        ]
      }
    },
    "multinomial_nb": {
      "validation": {
        "articles": 3824,
        "accuracy": 0.955021,
        "f1_fake": 0.949143,
        "f1_macro": 0.954412,
        "confusion_matrix_rows_fake_real": [
          [
            1605,
            93
          ],
          [
            79,
            2047
          ]
        ]
      },
      "test": {
        "articles": 3803,
        "accuracy": 0.949251,
        "f1_fake": 0.942781,
        "f1_macro": 0.948593,
        "confusion_matrix_rows_fake_real": [
          [
            1590,
            102
          ],
          [
            91,
            2020
          ]
        ]
      }
    },
    "linear_svm": {
      "validation": {
        "articles": 3824,
        "accuracy": 0.991893,
        "f1_fake": 0.990842,
        "f1_macro": 0.991785,
        "confusion_matrix_rows_fake_real": [
          [
            1677,
            21
          ],
          [
            10,
            2116
          ]
        ]
      },
      "test": {
        "articles": 3803,
        "accuracy": 0.992637,
        "f1_fake": 0.991716,
        "f1_macro": 0.992545,
        "confusion_matrix_rows_fake_real": [
          [
            1676,
            16
          ],
          [
            12,
            2099
          ]
        ]
      }
    }
  },
  "scikit_learn_version": "1.6.1",
  "pandas_version": "2.3.3",
  "limitations": "The dataset has source and topic confounding. Scores describe this dataset, not independent verification of news claims. LinearSVC margins are not probabilities."
}
(.venv) PS C:\Users\LapTop\Downloads\SIC\Capstone Project\sic-fake-news-detector> .\.venv\Scripts\python.exe -m unittest discover -s backend/tests
C:\Users\LapTop\Downloads\SIC\Capstone Project\sic-fake-news-detector\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
.......................................
----------------------------------------------------------------------
Ran 39 tests in 4.280s

OK