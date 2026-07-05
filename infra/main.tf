# RAGOps infrastructure — containerized service on AWS ECS Fargate.
#
# STATUS: SKELETON — NEVER APPLIED. It is `terraform validate`-able and shows I can
# express the deploy as code, but I have not stood it up, so I don't claim I have.
#
# Known limitation I would fix before applying: the vector index is a container-local
# PersistentClient on an ephemeral task volume. With desired_count > 1, each Fargate task
# holds its own index, so an /ingest handled by one task is invisible to a /query on
# another. The real fix is shared state — mount EFS at CHROMA_PATH, or (better) point at a
# managed vector database (e.g. a hosted Chroma / pgvector) and make the service stateless.
# Until then this is single-task infrastructure.
#
# Skeleton: ECR repo + ECS cluster + Fargate task/service. Bring your own VPC/subnets
# via variables (keeps this focused; wire an ALB + autoscaling as the next step).

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.region
}

resource "aws_ecr_repository" "ragops" {
  name                 = "ragops"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecs_cluster" "this" {
  name = "ragops"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_cloudwatch_log_group" "ragops" {
  name              = "/ecs/ragops"
  retention_in_days = 14
}

resource "aws_ecs_task_definition" "ragops" {
  family                   = "ragops"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn

  container_definitions = jsonencode([{
    name      = "ragops"
    image     = "${aws_ecr_repository.ragops.repository_url}:${var.image_tag}"
    essential = true
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "LLM_BASE_URL", value = var.llm_base_url },
      { name = "LLM_MODEL", value = var.llm_model },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ragops.name
        "awslogs-region"        = var.region
        "awslogs-stream-prefix" = "ragops"
      }
    }
    healthCheck = {
      command     = ["CMD-SHELL", "python -c \"import urllib.request;urllib.request.urlopen('http://localhost:8000/health')\" || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 20
    }
  }])
}

resource "aws_ecs_service" "ragops" {
  name            = "ragops"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.ragops.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = var.security_group_ids
    assign_public_ip = true
  }
  # TODO next: attach an ALB target group + aws_appautoscaling_target for autoscaling.
}
