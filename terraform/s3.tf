resource "aws_s3_bucket" "airspace" {
  bucket = "airspace-intelligence-${var.your_name}"
}

resource "aws_s3_bucket_versioning" "airspace" {
  bucket = aws_s3_bucket.airspace.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "airspace" {
  bucket = aws_s3_bucket.airspace.id
  rule {
    id     = "expire_raw_after_90_days"
    status = "Enabled"
    filter { prefix = "raw/" }
    expiration { days = 90 }
  }
}