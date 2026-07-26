import os
from pathlib import Path
import numpy as np
from PIL import Image
from django.core.management.base import BaseCommand
from django.core.files import File
from tests.models import RPMItem, RPMChoice

class Command(BaseCommand):
    help = 'Import CLEVR-Matrices with separate choice images'

    def add_arguments(self, parser):
        parser.add_argument('--source', type=str, required=True)
        parser.add_argument('--limit', type=int, default=20)

    def handle(self, *args, **options):
        source_dir = Path(options['source'])
        limit = options['limit']

        problem_map = {
            'problem1': ('Logic', 1),
            'problem2': ('Location', 2),
            'problem3': ('Count', 3),
        }

        output_dir = Path('media/clevr_extracted')
        output_dir.mkdir(parents=True, exist_ok=True)

        total = 0

        for folder_name, (problem_name, set_number) in problem_map.items():
            folder = source_dir / folder_name
            if not folder.exists():
                self.stdout.write(self.style.WARNING(f'{folder} not found'))
                continue

            files = sorted(list(folder.glob('prob_train_*.npz')) +
                           list(folder.glob('prob_val_*.npz')) +
                           list(folder.glob('prob_test_*.npz')))[:limit]

            self.stdout.write(f'\nProcessing {problem_name} ({len(files)} files)...')

            for npz_path in files:
                try:
                    data = np.load(npz_path)
                    images = data['image']          # (16, H, W, 3)
                    target = int(data['target'])

                    original_name = npz_path.stem
                    item_id = f"{problem_name.lower()}_{original_name}"

                    # Create the main 3×3 matrix image (with empty cell)
                    matrix_img = self.create_matrix_image(images[:8])
                    matrix_path = output_dir / f"{item_id}_matrix.png"
                    matrix_img.save(matrix_path)

                    item, created = RPMItem.objects.update_or_create(
                        item_id=item_id,
                        defaults={
                            'difficulty': set_number,
                            'correct_answer': str(target),
                            'explanation': f"CLEVR-Matrices – {problem_name}",
                            'set_number': set_number,
                        }
                    )

                    with open(matrix_path, 'rb') as f:
                        item.image.save(f"{item_id}_matrix.png", File(f), save=True)

                    # Save the 8 individual choice images
                    item.choices.all().delete()  # clean old ones
                    for idx in range(8):
                        choice_img = Image.fromarray(images[8 + idx].astype('uint8'))
                        choice_path = output_dir / f"{item_id}_choice_{idx}.png"
                        choice_img.save(choice_path)

                        choice = RPMChoice(item=item, index=idx)
                        with open(choice_path, 'rb') as f:
                            choice.image.save(f"{item_id}_choice_{idx}.png", File(f), save=True)

                    total += 1
                    status = "Created" if created else "Updated"
                    self.stdout.write(f"  ✓ {status}: {item_id} (correct: {target})")

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error {npz_path.name}: {e}"))

        self.stdout.write(self.style.SUCCESS(f'\nFinished! Imported {total} items.'))

    def create_matrix_image(self, context):
        """Create classic 3×3 grid with bottom-right cell empty"""
        panel_h, panel_w = 160, 200
        gap = 10
        margin = 15

        grid_w = 3 * panel_w + 2 * gap
        grid_h = 3 * panel_h + 2 * gap
        canvas = Image.new('RGB', (grid_w + 2*margin, grid_h + 2*margin), (245, 245, 245))

        positions = [
            (0,0), (1,0), (2,0),
            (0,1), (1,1), (2,1),
            (0,2), (1,2)          # bottom-right empty
        ]

        from PIL import ImageDraw
        draw = ImageDraw.Draw(canvas)

        for idx, (col, row) in enumerate(positions):
            x = margin + col * (panel_w + gap)
            y = margin + row * (panel_h + gap)

            if idx < len(context):
                img = Image.fromarray(context[idx].astype('uint8')).resize((panel_w, panel_h))
                canvas.paste(img, (x, y))
            else:
                # empty cell
                draw.rectangle([x, y, x+panel_w, y+panel_h], outline=(160,160,160), width=3)

        return canvas