resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  depends_on    = [ "aws_db_instance.db" ]
}

resource "aws_db_instance" "db" {
  allocated_storage    = 20
  engine               = "mysql"
  instance_class       = "db.t2.micro"
  username             = "foo"
  password             = "bar"
  parameter_group_name = "default.mysql5.6"
}

resource "aws_s3_bucket" "bucket" {
  bucket = "my-example-bucket"
}