resource "aws_iam_role" "lambda_role" {
  name = "LambdaRole-Airspace"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_s3" {
  name = "S3Policy-Airspace"
  role = aws_iam_role.lambda_role.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject", "s3:PutObject",
        "s3:ListBucket", "s3:DeleteObject"
      ]
      Resource = [
        "arn:aws:s3:::airspace-intelligence-${var.your_name}",
        "arn:aws:s3:::airspace-intelligence-${var.your_name}/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy" "lambda_secrets" {
  name = "SecretsPolicy-Airspace"
  role = aws_iam_role.lambda_role.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["secretsmanager:GetSecretValue"]
      Resource = [
        "arn:aws:s3:::airspace/opensky",
        "arn:aws:secretsmanager:${var.aws_region}:*:secret:airspace/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
