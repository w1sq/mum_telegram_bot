import random
import shutil
from glob import glob

def get_course_data(course_name:str, mode:str="quiz") -> list:
    output = []
    with open(f"courses/{course_name}/text.txt", "r", encoding="utf-8") as file:
        match mode:
            case "quiz":
                questions = list(map(lambda x: x.strip(), file.read().split("---")))
                for question in questions:
                    question_text, *answers = question.split("\n")
                    question_data = {"question": question_text, "answers":[], "correct": ""}
                    for answer in answers:
                        if answer.startswith("!"):
                            answer = answer[1:]
                            question_data["correct"] = answer
                        question_data["answers"].append(answer.strip())
                    output.append(question_data)
    random.shuffle(output)
    return output

def get_courses_names() -> list[str]:
    courses = []
    for course in glob("courses/*/", recursive = True):
        courses.append(course.split("/")[1])
    return courses

def get_course_info(course_name:str) -> str:
    with open(f"courses/{course_name}/info.txt", "r", encoding="utf-8") as file:
        return file.read()

def delete_course(course_name:str):
    shutil.rmtree(f"courses/{course_name}")


if __name__ == "__main__":
    print(get_courses_names())