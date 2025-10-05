"""
Custom management command for production database migration.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Run production database migrations with safety checks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting production database migration...')
        )

        # Check if we're in production mode
        if settings.DEBUG:
            self.stdout.write(
                self.style.WARNING(
                    'WARNING: DEBUG is True. This should be False in production.'
                )
            )

        # Check database configuration
        db_config = settings.DATABASES['default']
        self.stdout.write(f"Database Engine: {db_config['ENGINE']}")
        self.stdout.write(f"Database Name: {db_config['NAME']}")
        
        if 'postgresql' in db_config['ENGINE']:
            self.stdout.write(f"Database Host: {db_config['HOST']}")
            self.stdout.write(f"Database Port: {db_config['PORT']}")

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
            call_command('migrate', '--dry-run', verbosity=2)
        else:
            # Run migrations
            self.stdout.write('Running migrations...')
            call_command('migrate', verbosity=2)
            
            # Load initial data if needed
            self.stdout.write('Loading initial data...')
            try:
                call_command('load_food_data', verbosity=2)
                self.stdout.write(
                    self.style.SUCCESS('Food data loaded successfully')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error loading food data: {e}')
                )
            
            # Generate embeddings
            self.stdout.write('Generating embeddings...')
            try:
                call_command('generate_embeddings', verbosity=2)
                self.stdout.write(
                    self.style.SUCCESS('Embeddings generated successfully')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error generating embeddings: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS('Production database migration completed!')
        )
