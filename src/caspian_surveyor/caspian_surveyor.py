"""Launch the Caspian Surveyor core process."""
from caspian_surveyor.application import CaspianSurveyorApplication

def main() -> None:
    CaspianSurveyorApplication().run()

if __name__ == "__main__":
    main()