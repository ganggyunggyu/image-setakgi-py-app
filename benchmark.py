"""이미지 처리 성능 벤치마크"""
import time
import multiprocessing as mp
from pathlib import Path
from dataclasses import dataclass

from PIL import Image
from app.core.random_transform import generate_random_options, RandomTransformConfig
from app.core.image_ops import apply_transforms
from app.core.save_output import save_transformed_image


@dataclass
class BenchmarkResult:
    total_images: int
    total_time: float
    avg_time_per_image: float
    images_per_second: float
    total_megapixels: float


def _init_worker() -> None:
    """워커 프로세스별 OpenCV 스레드 1개로 제한"""
    try:
        import cv2

        cv2.setNumThreads(1)
    except Exception:
        return


def process_single_image(args):
    """단일 이미지 처리 (멀티프로세스용)"""
    img_path, output_dir, idx, config_dict = args

    start = time.time()
    original = Image.open(img_path)
    w, h = original.size
    megapixels = (w * h) / 1_000_000

    config = RandomTransformConfig(**config_dict)
    options = generate_random_options(config, w, h)

    transformed = apply_transforms(
        original,
        crop=options.get('crop', 0),
        rotation=options.get('rotation', 0),
        noise=options.get('noise', 0),
        brightness=options.get('brightness', 0),
        perspective_corners=options.get('corners'),
    )

    save_transformed_image(transformed, output_dir, f'bench_{idx}.jpg', output_format='jpeg')
    elapsed = time.time() - start

    return {
        'path': str(img_path),
        'size': f'{w}x{h}',
        'megapixels': megapixels,
        'time': elapsed
    }


def run_sequential(images: list, output_dir: Path, config: RandomTransformConfig) -> BenchmarkResult:
    """순차 처리"""
    output_dir.mkdir(parents=True, exist_ok=True)
    config_dict = {
        'crop_range': config.crop_range,
        'rotation_range': config.rotation_range,
        'noise_range': config.noise_range,
        'perspective_range': config.perspective_range,
        'date_days_back': config.date_days_back,
    }

    args = [(img, output_dir, i, config_dict) for i, img in enumerate(images)]

    total_mp = 0
    start = time.time()
    for a in args:
        result = process_single_image(a)
        total_mp += result['megapixels']
    total_time = time.time() - start

    return BenchmarkResult(
        total_images=len(images),
        total_time=total_time,
        avg_time_per_image=total_time / len(images),
        images_per_second=len(images) / total_time,
        total_megapixels=total_mp
    )


def run_parallel(images: list, output_dir: Path, config: RandomTransformConfig, n_workers: int = None) -> BenchmarkResult:
    """병렬 처리"""
    if n_workers is None:
        n_workers = mp.cpu_count()

    output_dir.mkdir(parents=True, exist_ok=True)

    config_dict = {
        'crop_range': config.crop_range,
        'rotation_range': config.rotation_range,
        'noise_range': config.noise_range,
        'perspective_range': config.perspective_range,
        'date_days_back': config.date_days_back,
    }

    args = [(img, output_dir, i, config_dict) for i, img in enumerate(images)]

    start = time.time()
    chunk_size = max(1, len(args) // (n_workers * 2) or 1)
    with mp.Pool(processes=n_workers, initializer=_init_worker) as pool:
        results = list(
            pool.imap_unordered(
                process_single_image,
                args,
                chunksize=chunk_size,
            )
        )
    total_time = time.time() - start

    total_mp = sum(r['megapixels'] for r in results)

    return BenchmarkResult(
        total_images=len(images),
        total_time=total_time,
        avg_time_per_image=total_time / len(images),
        images_per_second=len(images) / total_time,
        total_megapixels=total_mp
    )


def print_report(seq_result: BenchmarkResult, par_result: BenchmarkResult, n_cores: int):
    """보고서 출력"""
    print("\n" + "=" * 60)
    print("이미지 처리 성능 벤치마크 보고서")
    print("=" * 60)

    print(f"\n📊 테스트 환경")
    print(f"  - CPU 코어: {n_cores}개")
    print(f"  - 이미지 수: {seq_result.total_images}장")
    print(f"  - 총 메가픽셀: {seq_result.total_megapixels:.1f}MP")

    print(f"\n⏱️ 순차 처리 (Single Process)")
    print(f"  - 총 시간: {seq_result.total_time:.2f}초")
    print(f"  - 평균: {seq_result.avg_time_per_image:.2f}초/장")
    print(f"  - 처리량: {seq_result.images_per_second:.2f}장/초")

    print(f"\n🚀 병렬 처리 (Multi Process, {n_cores} workers)")
    print(f"  - 총 시간: {par_result.total_time:.2f}초")
    print(f"  - 평균: {par_result.avg_time_per_image:.2f}초/장")
    print(f"  - 처리량: {par_result.images_per_second:.2f}장/초")

    speedup = seq_result.total_time / par_result.total_time
    print(f"\n📈 성능 향상")
    print(f"  - 속도 향상: {speedup:.1f}x")
    print(f"  - 시간 절약: {seq_result.total_time - par_result.total_time:.1f}초 ({(1 - par_result.total_time/seq_result.total_time) * 100:.0f}%)")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    input_dir = Path('test_input')
    output_dir = Path('test_output/benchmark')
    output_dir.mkdir(exist_ok=True)

    images = list(input_dir.glob('*.jpeg')) + list(input_dir.glob('*.jpg'))
    n_cores = mp.cpu_count()

    print(f"🔍 이미지 {len(images)}장 발견")
    print(f"🖥️ CPU 코어 {n_cores}개 사용 가능\n")

    config = RandomTransformConfig()

    print("⏳ 순차 처리 테스트 중...")
    seq_result = run_sequential(images, output_dir / 'seq', config)

    print("⏳ 병렬 처리 테스트 중...")
    par_result = run_parallel(images, output_dir / 'par', config, n_cores)

    print_report(seq_result, par_result, n_cores)
