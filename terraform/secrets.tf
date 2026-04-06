resource "aws_secretsmanager_secret" "opensky" {
  name = "airspace/opensky"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret" "databricks" {
  name = "airspace/databricks"
  recovery_window_in_days = 0
}