# Dataset provenance

`sms_spam_uci.csv` is generated from the UCI Machine Learning Repository's **SMS Spam Collection** (Almeida & Hidalgo, 2011), DOI `10.24432/C5CC84`, licensed under CC BY 4.0. It contains 5,574 real labeled SMS messages.

`demo_dataset.csv` is a small NAZAR-authored India-context supplement. It is used only to add local scam vocabulary; reported user content is not automatically promoted into training data because that would permit data poisoning and unreviewed personal data ingestion.

Regenerate the public dataset with `python ml/import_uci_sms.py`.
