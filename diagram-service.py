import hcl2
import uuid
from diagrams import Diagram, Cluster, Edge

# Import AWS node classes from the diagrams library.
from diagrams.aws.compute import EC2, Lambda, ECS, AutoScaling, ECR
from diagrams.aws.database import RDS, Dynamodb, Redshift, ElastiCache
from diagrams.aws.network import ELB, ALB, VPC, CloudFront, Route53
from diagrams.aws.storage import S3, EFS
from diagrams.aws.security import IAM
from diagrams.aws.devtools import Codebuild
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.management import Cloudformation

# Map Terraform resource types to a tuple: (Diagrams Node Class, Cluster/Category Name)
RESOURCE_MAP = {
    # Compute / Containers
    "aws_instance": (EC2, "Compute"),
    "aws_lambda_function": (Lambda, "Compute"),
    "aws_ecs_cluster": (ECS, "Compute"),
    "aws_autoscaling_group": (AutoScaling, "Compute"),
    "aws_ecr_repository": (ECR, "Containers"),
    
    # Databases
    "aws_db_instance": (RDS, "Database"),
    "aws_dynamodb_table": (Dynamodb, "Database"),
    "aws_redshift_cluster": (Redshift, "Database"),
    "aws_elasticache_cluster": (ElastiCache, "Database"),
    
    # Network & Content Delivery
    "aws_elb": (ELB, "Network"),
    "aws_alb": (ALB, "Network"),
    "aws_vpc": (VPC, "Network"),
    "aws_cloudfront_distribution": (CloudFront, "Content Delivery"),
    "aws_route53_zone": (Route53, "Network"),
    
    # Storage
    "aws_s3_bucket": (S3, "Storage"),
    "aws_efs_file_system": (EFS, "Storage"),
    
    # Integration / Messaging
    "aws_sqs_queue": (SQS, "Integration"),
    "aws_sns_topic": (SNS, "Integration"),
    
    # Security
    "aws_iam_role": (IAM, "Security"),
    
    # DevOps
    "aws_codebuild_project": (Codebuild, "DevOps"),
    
    # Management
    "aws_cloudformation_stack": (Cloudformation, "Management"),
}

def parse_terraform(terraform_content):
    """
    Parse Terraform HCL content using python-hcl2.
    """
    try:
        return hcl2.loads(terraform_content)
    except Exception as e:
        raise ValueError(f"Error parsing Terraform file: {e}")
    
def extract_resources(parsed_data):
    """
    Extracts resources from parsed Terraform data.
    The 'resource' key is expected to be a list of dictionaries.
    Returns a dictionary where keys are composite IDs like 'aws_instance.example'
    and values contain resource details.
    """
    resources = {}
    resources_data = parsed_data.get("resource", [])
    
    if isinstance(resources_data, list):
        for resource_block in resources_data:
            # Each resource_block should be a dictionary where the key is the resource type.
            if isinstance(resource_block, dict):
                for resource_type, instances in resource_block.items():
                    # instances should be a dictionary where keys are resource names.
                    if isinstance(instances, dict):
                        for resource_name, resource_config in instances.items():
                            resource_id = f"{resource_type}.{resource_name}"
                            if resource_type in RESOURCE_MAP:
                                node_class, cluster_name = RESOURCE_MAP[resource_type]
                                resources[resource_id] = {
                                    "type": resource_type,
                                    "name": resource_name,
                                    "config": resource_config,
                                    "node_class": node_class,
                                    "cluster": cluster_name,
                                }
                            else:
                                print(f"Warning: No mapping for resource type '{resource_type}' (resource: {resource_id}). Skipping.")
                    else:
                        print(f"Expected dict for instances under resource type '{resource_type}', got {type(instances)}")
            else:
                print(f"Expected dict in resource block, got {type(resource_block)}")
    elif isinstance(resources_data, dict):
        # Fallback if resources_data is already a dict.
        for resource_type, instances in resources_data.items():
            for resource_name, resource_config in instances.items():
                resource_id = f"{resource_type}.{resource_name}"
                if resource_type in RESOURCE_MAP:
                    node_class, cluster_name = RESOURCE_MAP[resource_type]
                    resources[resource_id] = {
                        "type": resource_type,
                        "name": resource_name,
                        "config": resource_config,
                        "node_class": node_class,
                        "cluster": cluster_name,
                    }
                else:
                    print(f"Warning: No mapping for resource type '{resource_type}' (resource: {resource_id}). Skipping.")
    else:
        print(f"Unexpected structure for 'resource': {type(resources_data)}")
    
    return resources

def generate_diagram_from_terraform(terraform_file_path, diagram_title="Terraform Diagram"):
    """
    Reads a Terraform file, parses it, and generates a PNG diagram using the diagrams library.
    The diagram uses:
      - Nodes: Representing AWS resources.
      - Clusters: Grouping resources by category (e.g., Compute, Database, etc.).
      - Edges: Connecting resources based on Terraform's `depends_on` attribute.
    """
    # Read the Terraform file.
    with open(terraform_file_path, "r") as f:
        terraform_content = f.read()
    
    parsed_data = parse_terraform(terraform_content)

    # Generate a unique filename for the diagram.
    unique_id = uuid.uuid4().hex
    diagram_filename = f"terraform_diagram_{unique_id}"

    # Build a resource dictionary from the parsed Terraform data.
    # The key is a composite ID like "aws_instance.example"
    resources = extract_resources(parsed_data)

    # Group resources by their cluster (category).
    clusters = {}
    for resource_id, resource in resources.items():
        cluster_name = resource["cluster"]
        clusters.setdefault(cluster_name, []).append(resource_id)

    # Dictionary to hold the created diagram nodes.
    nodes = {}

    # Build the diagram.
    with Diagram(diagram_title, filename=diagram_filename, outformat="png", show=False):
        # Create clusters and add nodes.
        for cluster_name, resource_ids in clusters.items():
            with Cluster(cluster_name):
                for res_id in resource_ids:
                    resource = resources[res_id]
                    # Instantiate a node using the mapped node class and resource name.
                    nodes[res_id] = resource["node_class"](resource["name"])
        
        # Create edges between nodes if a resource has a 'depends_on' attribute.
        for resource_id, resource in resources.items():
            depends_on = resource["config"].get("depends_on", [])
            if isinstance(depends_on, list):
                for dep in depends_on:
                    # Terraform dependencies are usually in the form "aws_resource.resource_name"
                    if dep in nodes and resource_id in nodes:
                        # You can customize edge styles by using the Edge class.
                        nodes[dep] >> nodes[resource_id]
                    else:
                        print(f"Warning: Dependency '{dep}' not found for resource '{resource_id}'.")
            else:
                if depends_on:
                    print(f"Warning: 'depends_on' for {resource_id} is not a list. Skipping dependency edges.")

    output_png = diagram_filename + ".png"
    print(f"Diagram generated: {output_png}")
    return output_png

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python terraform_to_diagram.py path/to/terraform_file.tf")
        sys.exit(1)
    
    terraform_file = sys.argv[1]
    generate_diagram_from_terraform(terraform_file)
