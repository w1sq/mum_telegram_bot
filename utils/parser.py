import random

def read_file(path:str, mode:str="quiz") -> dict:
    output = {}
    with open(path, "r", encoding="utf-8") as file:
        match mode:
            case "quiz":
                questions = file.read().split("---")
                for question in questions:
                    question_text, answers = question.split("\n")
                    output[question_text] = {"answers":[], "correct": ""}
                    for answer in answers:
                        if answer.startswith("!"):
                            answer = answer[1:]
                            output[question_text]["correct"] = answer
                        output["questions"][question_text].append(answer)
                    random.shuffle(output["questions"][question_text])

    return output

                    
