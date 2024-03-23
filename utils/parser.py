import os
import shutil
from glob import glob


def get_course_data(course_name: str, mode: str = "quiz") -> list:
    output = []
    course_path = get_course_path(course_name)
    with open(f"{course_path}/text.txt", "r", encoding="utf-8") as file:
        match mode:
            case "quiz":
                questions = list(map(lambda x: x.strip(), file.read().split("---")))
                for question in questions:
                    if question.startswith("Reading\n"):
                        output.append(question)
                    elif question.startswith("Listening\n"):
                        output.append(question)
                    questions_number = len(question.split("\n"))
                    if questions_number == 5:
                        strings = question.split("\n")
                        answers = strings[1:]
                        question_data = {
                            "question": strings[0],
                            "answers": [],
                            "correct": "",
                        }
                        for answer in answers:
                            if answer.startswith("!"):
                                answer = answer[1:]
                                question_data["correct"] = answer.strip()[:100]
                            question_data["answers"].append(answer.strip()[:100])
                        output.append(question_data)
                    elif questions_number == 6:
                        strings = question.split("\n")
                        answers = strings[1:-1]
                        question_data = {
                            "question": strings[0],
                            "hint": strings[-1][:200],
                            "answers": [],
                            "correct": "",
                        }
                        for answer in answers:
                            if answer.startswith("!"):
                                answer = answer[1:]
                                question_data["correct"] = answer.strip()[:100]
                            question_data["answers"].append(answer.strip()[:100])
                        output.append(question_data)
    return output


def get_course_path(course_name: str):
    for root, dirs, files in os.walk("courses/"):
        if course_name in dirs:
            return os.path.join(root, course_name)
    return None


def get_sections_names() -> list[str]:
    sections = []
    for course in glob("courses/*/", recursive=True):
        sections.append(course.split("/")[1])
    return sections


def get_courses_names(section: str) -> list[str]:
    courses = []
    for course in glob(f"courses/{section}/*/", recursive=True):
        courses.append(course.split("/")[2])
    return courses


def get_course_info(course_name: str) -> str:
    course_path = get_course_path(course_name)
    with open(f"{course_path}/info.txt", "r", encoding="utf-8") as file:
        return file.read()


def delete_course(course_name: str):
    course_path = get_course_path(course_name)
    shutil.rmtree(course_path)


if __name__ == "__main__":
    print(get_course_path("Loans and Credit"))
