import sys
import argparse
import json
import subprocess
import pandas as pd
from types import ModuleType



def run(text, input_value):
    try:
        results = subprocess.Popen(
            [
                "python",
                "skill_test/run_sol1.py",
                "--solution",
                text,
                "--input",
                json.dumps(input_value)
            ],
            stdout= subprocess.PIPE
        )
        p = results.communicate()[0].strip().decode()
        if p=="false":
            return False
        if p=="true":
            return True
        if p!="":
            try:
                p=eval(p)
            except:
                pass
            if p=="false":
                return False
            if p=="true":
                return true
            try:
                try:
                    return json.loads(json.loads(json.loads(p)))
                except Exception as e2:
                    return json.loads(json.loads(p))
            except Exception as e1:
                return p
        else:
            return "Time Out"
    except Exception as r_e:
        return "Error"



def check_valid_submission(text):
    if "print" in text:
        return False, "prints are not allowed"
    if "input" in text:
        return False, "input are not allowed"
    if "import" in text:
        lines = [l.strip().replace(" ","") for l in text.split("\n") if "import" in l]
        lines = [l for l in lines if "importre"!=l]
        if lines:
            return False, "importing libraries is not allowed"
    return True, ""


def evaluate_solution(text, groundtruths_dict, score):
    score_per_unit = score/sum([v.get("score_points",1) for k,v in groundtruths_dict.items()])
    results = {}
    results["obtained_score"] = 0
    for k,v in groundtruths_dict.items():
        results[k] = {}
        s = score_per_unit*v.get("score_points",1)
        out=""
        try:
            out = run(text, json.dumps(v["input"]))
            if out=="Time Out":
                results[k]["status"] = "Time Out"
                results[k]["score"] = "0/"+str(round(s,2))
            elif out==v["output"]:
                results[k]["status"] = "Passed"
                results[k]["score"] = str(round(s,2))+"/"+str(round(s,2))
                results["obtained_score"] += s
            elif out=="Error":
                results[k]["status"] = "Error"
                results[k]["score"] = "0/"+str(round(s,2))
            else:
                results[k]["status"] = "Failed"
                results[k]["score"] = "0/"+str(round(s,2))
        except:
            results[k]["status"] = "Error"
            results[k]["score"] = "0/"+str(round(s,2))
        if v["hidden"]:
            results[k]["input"] = "Hidden"
            results[k]["output"] = "Hidden"
            results[k]["expected_output"] = "Hidden"
        else:
            results[k]["input"] = v["input"]
            results[k]["output"] = out
            results[k]["expected_output"] = v["output"]
    return results


def disp(r):
    r_dict = {
        "Test Case": [],
        "Input": [],
        "Expected Output": [],
        "Output": [],
        "Status": [],
        "Score": [],
    }
    for k,v in r.items():
        if k!="obtained_score":
            r_dict["Test Case"] += [k]
            r_dict["Input"] += [v.get("input","N/A")]
            r_dict["Expected Output"] += [v.get("expected_output","N/A")]
            r_dict["Output"] += [v.get("output","N/A")]
            r_dict["Status"] += [v.get("status","N/A")]
            r_dict["Score"] += [v.get("score","N/A")]
    r_dict["Test Case"] += ["Total Score"]
    r_dict["Input"] += [""]
    r_dict["Expected Output"] += [""]
    r_dict["Output"] += [""]
    r_dict["Status"] += [""]
    r_dict["Score"] += [r.get("obtained_score","N/A")]
    df = pd.DataFrame.from_dict(r_dict)
    """mydict = {
    "df": df.to_html()
    }"""
    return df.to_html(classes='table table-stripped')


parser = argparse.ArgumentParser()
parser.add_argument('--solution', type=str)
parser.add_argument('--score', type=str)
parser.add_argument('--groundtruths', type=str)

arg = parser.parse_args()
answer = arg.solution
score = float(arg.score)
groundtruths = json.loads(arg.groundtruths)


obt_marks = 0
mod = ModuleType('my_module', 'doc string here')
sys.modules['my_module'] = mod
valid_to_submit_flag, valid_to_submit_message = check_valid_submission(answer)
if valid_to_submit_flag:
    try:
        exec(answer, mod.__dict__)
        sys.modules['my_module'] = mod
    except:
        valid_to_submit_flag = False
        text = "def solution():\n    return n"
    r1=evaluate_solution(answer, groundtruths, score)
    blow=disp(r1)
    obt_marks = r1.get("obtained_score",0)
else:
    df = pd.DataFrame.from_dict({"Error":[valid_to_submit_message]})
    blow = df.to_html(classes='table table-stripped')


r=(valid_to_submit_flag,blow, obt_marks)
print(json.dumps(r))
