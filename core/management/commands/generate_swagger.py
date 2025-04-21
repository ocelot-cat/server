from django.core.management.base import BaseCommand
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.renderers import OpenAPIRenderer, YAMLRenderer


class Command(BaseCommand):
    help = "Generate Swagger documentation in JSON or YAML format"

    def add_arguments(self, parser):
        parser.add_argument("--format", choices=["json", "yaml"], default="json")

    def handle(self, *args, **options):
        generator = OpenAPISchemaGenerator()
        schema = generator.get_schema()

        if options["format"] == "yaml":
            renderer = YAMLRenderer()
            output = renderer.render(schema)
            with open("swagger.yaml", "w", encoding="utf-8") as f:
                f.write(output.decode("utf-8"))
            self.stdout.write(self.style.SUCCESS("Successfully generated swagger.yaml"))
        else:
            renderer = OpenAPIRenderer()
            output = renderer.render(schema)
            with open("swagger.json", "w", encoding="utf-8") as f:
                f.write(output.decode("utf-8"))
            self.stdout.write(self.style.SUCCESS("Successfully generated swagger.json"))
