"""Launch the Caspian Surveyor core process."""
from multiprocessing import freeze_support

def main() -> None:
    from caspian_surveyor.application import CaspianSurveyorApplication
    CaspianSurveyorApplication().run()


if __name__ == "__main__":
    freeze_support()
    main()