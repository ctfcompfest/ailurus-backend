from and_platform.core.challenge import get_challenges_directory
import pip

def install_checker_dependencies():
    chall_dir = get_challenges_directory()
    for path in chall_dir.iterdir():
        if not path.is_dir() or not path.name.startswith("chall-"):
            continue
        
        req_path = path.joinpath("test", "requirements.txt")
        if not req_path.exists(): continue

        pip.main(["install", "-r", req_path.as_posix()])