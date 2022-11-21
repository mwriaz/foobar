import os
import io
import json
import traceback
import subprocess
import random
import string
import pandas as pd

from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import logout
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponse
from django.http import Http404
from skill_test.models import Questions
from skill_test.models import Tests
from skill_test.models import Users
from skill_test.models import Batches
from skill_test.models import Results




def generate_passwrod():
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for i in range(7)) + random.choice(string.punctuation)


def download_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404


def download_df_as_csv(df,filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename='+filename
    df.to_csv(path_or_buf=response,sep=';',float_format='%.2f',index=False,decimal=",")
    return response


def validate(text, test, score):
    results = subprocess.Popen(
        [
            "python",
#             "home/validate_solution.py", # for linux and mac (optimized for speed)
            "skill_test/validate_solution_w.py", # for windows, linux and mac (not optimized in speed)
            "--solution",
            text,
            "--score",
            str(score),
            "--groundtruths",
            json.dumps(test)
        ],
        stdout= subprocess.PIPE
    )
    return json.loads(results.communicate()[0].strip().decode())


def logout_view(request):
    if not request.META.get('HTTP_REFERER'):
        raise Http404
    logout(request)
    return redirect(index)


def index(request):
    if request.method == "POST":
        if "login" in request.POST:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
            else:
                messages.error(request, "Unable to Login")
        if "proceed" in request.POST:
            opt = request.POST.get("opt")
            if "test" in opt:
                return redirect(tests)
            elif "result" in opt:
                return redirect(results)
            else:
                messages.error(request, "Write only 'run test.py' or 'run result.py'!")
    return render(request, 'index.html', {})

    
def test_manage(request, op=1):
    if not request.META.get('HTTP_REFERER'):
        return redirect(index)
    if not request.user.is_authenticated:
        return redirect(index)
    
    tests = Tests.objects.all()
    all_t_ids = [t.t_id for t in tests]
    available_t_ids = [t.t_id for t in tests if t.is_open]
    not_available_t_ids = [t.t_id for t in tests if not t.is_open]
    print("available_t_ids:",available_t_ids)
    print("not_available_t_ids:",not_available_t_ids)
    if request.method == "POST":
        if "e_test" in request.POST:
            op = 1
        if "d_test" in request.POST:
            op = 2
        if "a_test" in request.POST:
            op = 3
        if "a_question" in request.POST:
            op = 4
        if "enable_test" in request.POST:
            op = int(request.POST.get("enable_test"))
            t_id = request.POST.get("t_id")
            if t_id in not_available_t_ids:
                t = Tests.objects.filter(t_id=t_id)[0]
                t.is_open=True
                t.save()
                messages.success(request, "Enabled")
            else:
                messages.error(request, "Unable to Enable")
        if "disable_test" in request.POST:
            op = int(request.POST.get("disable_test"))
            t_id = request.POST.get("t_id")
            if t_id in available_t_ids:
                t = Tests.objects.filter(t_id=t_id)[0]
                t.is_open=False
                t.save()
                messages.success(request, "Disabled")
            else:
                messages.error(request, "Unable to Disable")
        if "add_test" in request.POST:
            op = int(request.POST.get("add_test"))
            t_id = request.POST.get("t_id")
            is_open = request.POST.get("enable")=="enable"
            if t_id not in all_t_ids:
                print(op, t_id, is_open)
                t = Tests(t_id=t_id, is_open=is_open)
                t.save()
                messages.success(request, "Added")
            else:
                messages.error(request, "Already Exists with same name. Please choose different name.")
        if "add_q" in request.POST:
            op = int(request.POST.get("add_q"))
            t_id = request.POST.get("t_ids")
            print("t_id:",t_id)
            statement = request.POST.get("statement")
            solution = request.POST.get("solution")
            score = request.POST.get("score")
            inp = request.POST.getlist("inp")
            out = request.POST.getlist("out")
            points = request.POST.getlist("points")
            h = request.POST.getlist("h")
            print(len(inp),len(out),len(points),len(h))
            try:
                gts = {}
                for i in range(10):
                    if inp[i]:
                        gts[i+1] = {}
                        try:
                            gts[i+1]["input"] = eval(inp[i])
                        except:
                            gts[i+1]["input"] = inp[i]
                        try:
                            gts[i+1]["output"] = eval(out[i])
                        except:
                            gts[i+1]["output"] = out[i]
                        gts[i+1]["hidden"] = str(i+1) in h
                        gts[i+1]["score_points"] = int(points[i])
                try:
                    score = float(score)
                    try:
                        json.dumps(gts)
                        print(gts)
                        try:
                            exec(solution)
                            blow_flag, blow, obt_marks = validate(solution, gts, score)
                            print(blow_flag, blow, obt_marks)
                            questions = Questions.objects.filter(t_id=t_id)
                            q_id = len(questions)+1
                            if round(float(score),2)==round(float(obt_marks),2):
                                q = Questions(q_id=q_id,t_id=t_id, groundtruths=json.dumps(gts), statement=statement, score=score, solution=solution)
                                q.save()
                                messages.success(request, "`Question Added Successfully")
                            else:
                                messages.error(request, "Solution could not be verified on test cases. Plese check.")
                        except:
                            print(traceback.print_exc())
                            messages.error(request, "There is some issue in solution")
                    except:
                        messages.error(request, "There is some issue in grountruths")
                except:
                    messages.error(request, "Please provide score in int/float")
            except:
                print(traceback.print_exc())
                
    
    tests = Tests.objects.all()
    all_t_ids = [t.t_id for t in tests]
    available_t_ids = [t.t_id for t in tests if t.is_open]
    not_available_t_ids = [t.t_id for t in tests if not t.is_open]

    return render(
        request,
        'test_manage.html',
        {
            "op":op,
            "t_ids": available_t_ids,
            "n_t_ids": not_available_t_ids,
            "all_t_ids": all_t_ids
        }
    )
    
    
        
def tests(request):
    if not request.META.get('HTTP_REFERER'):
        return redirect(index)
    if not request.user.is_authenticated:
        return redirect(index)
    tests = Tests.objects.all()
    t_ids = [t.t_id for t in tests if t.is_open]
    if request.user.is_superuser:
        allowed_test = t_ids
        email = request.user.username+"@super.user"
    else:
        username = request.user.username
        u = Users.objects.filter(username=username)[0]
        email = u.email
        allowed_test = json.loads(u.allowed_test)
    t_ids = [t.t_id for t in tests if t.t_id in allowed_test]
    t_ids = [t_id for t_id in t_ids if Questions.objects.filter(t_id=t_id)]
    if request.method == "POST":
        agree = bool(request.POST.get("agree"))
        t_id = request.POST.get("t_id")
        if agree:
            if t_id:
                return redirect(take_test,t_id=t_id)
            else:
                messages.error(request, "No Test found!")
        else:
            messages.error(request, "Please read the instructions and mark the checkbox")
    return render(
        request,
        'tests.html',
        {
            "t_ids":t_ids
        }
    )

def take_test(request, t_id="", q_id=1):
    if not request.META.get('HTTP_REFERER'):
        return redirect(index)
    if not request.user.is_authenticated:
        return redirect(index)
    if request.method == "POST":
        if "previous" in request.POST:
            t_id, q_id = request.POST.get("previous").split(",")
        if "next" in request.POST:
            t_id, q_id = request.POST.get("next").split(",")
        if "verify" in request.POST:
            t_id, q_id = request.POST.get("verify").split(",")
        if "submit" in request.POST:
            t_id, q_id = request.POST.get("submit").split(",")
        q_id = int(q_id)
    status = "Un Attempted"
    testcases_flag = False
    testcases = ""
    prefilled_solution = "def solution(x):\n    # return your code"
    questions = Questions.objects.filter(t_id=t_id)
    total_questions = len(questions)
    if q_id>total_questions:
        messages.error(request, "Technical Error!")
        return redirect(index)
    username = request.user.username
    if request.user.is_superuser:
        email = username+"@super.user"
    else:
        u = Users.objects.filter(username=username)[0]
        email = u.email
        allowed_test = json.loads(u.allowed_test)
        if t_id not in allowed_test:
            messages.error(request, "You are not allowed to attempt this test!")
            return redirect(index)
    if request.method == "POST":
        if "previous" in request.POST:
            q_id -= 1
            if q_id<1:
                q_id = 1
            print(q_id,t_id,"previous")
        if "next" in request.POST:
            q_id += 1
            if q_id>=total_questions:
                q_id = total_questions
            print(q_id,t_id,"next")
        if "verify" in request.POST or "submit" in request.POST:
            try:
                r_flag = False
                results = Results.objects.filter(t_id=t_id, email=email, q_id=questions[q_id-1].q_id)
                if results:
                    r_flag = results[0]
                    if r_flag.t_cases>0:
                        status = "Submitted"
                    else:
                        status = "Not Submitted"
            except:
                pass

            if status=="Submitted":
                messages.error(request, "Already submitted!\nYou cant submit a solution twice.")
            else:
                solution = request.POST.get("solution")
                groundtruths = json.loads(questions[q_id-1].groundtruths)
                score = int(questions[q_id-1].score)
                solution_flag, testcases, obt_marks = validate(solution, groundtruths, score)
                testcases = testcases.replace('<table border="1"','<table style="border-style:dashed;border-color:#fffffF;border-width:thin;height:100px;width:100%;"')
                testcases = testcases.replace('<th>','<th align="center">')
                testcases_flag = True
                if solution_flag:
                    t_cases = len(groundtruths)
                    p_cases = testcases.count("Passed")
                    if "submit" in request.POST:
                        if r_flag:
                            r = r_flag
                            r.obtained_marks = obt_marks
                            r.soultion = solution
                            r.t_cases = t_cases
                            r.p_cases = p_cases
                        else:
                            r = Results(t_id=t_id, q_id=q_id, obtained_marks=obt_marks, total_marks=score, email=email, solution=solution, t_cases=t_cases, p_cases=p_cases)
                        r.save()
                        messages.success(request, 'Your solution has been submitted!')
                    else:
                        if r_flag:
                            r = r_flag
                            r.soultion = solution
                            r.p_cases = p_cases
                        else:
                            r = Results(t_id=t_id, q_id=q_id, obtained_marks=0, total_marks=score, email=email, solution=solution, t_cases=0, p_cases=0)
                        r.save()
                        status = "Submitted"
                        messages.success(request, 'Your solution has been Verified!\nPress submit button to submit it.')
                else:
                    status = "Not Submitted"
                    messages.error(request, 'Unsuccessful!\nRemove errors from your code!')
    try:
        results = Results.objects.filter(t_id=t_id, email=email, q_id=questions[q_id-1].q_id)
        if results:
            results = results[0]
            prefilled_solution = results.solution
            if results.t_cases>0:
                status = "Submitted"
            else:
                status = "Not Submitted"
    except:
        pass
    
    return render(
        request,
        'take_test.html',
        {
            "t_id": t_id,
            "q_id": q_id,
            "t_questions": total_questions,
            "u_email": email,
            "status": status,
            "statement": questions[q_id-1].statement,
            "score": int(questions[q_id-1].score),
            "testcases_flag": testcases_flag,
            "prefilled_solution": prefilled_solution,
            "testcases": testcases
        }
    )

def users_m(request, op=1, batches=[], all_t_ids=[]):
    try:
        if not request.META.get('HTTP_REFERER'):
            return redirect(index)
        if not request.user.is_authenticated:
            return redirect(index)
        tests = Tests.objects.all()
        all_t_ids = [t.t_id for t in tests]
        all_batches = Batches.objects.all()
        batches = [b.b_id for b in all_batches if b.is_open]
        if request.method == "POST":
            if "a_user" in request.POST:
                op = 1
            if "d_user" in request.POST:
                op = 2
            if "a_t_u" in request.POST:
                op = 3
            if "a_t_b" in request.POST:
                op = 4
            if "c_batch" in request.POST:
                op = 5
            if "d_batch" in request.POST:
                op = 6
            if "download_csv" in request.POST:
                op = int(request.POST.get("download_csv"))
                return download_file("templates/batch_template.csv")
            if "add_user" in request.POST:
                op = int(request.POST.get("add_user"))
                name = request.POST.get("full_name")
                email = request.POST.get("email")
                phone = request.POST.get("contact_number")
                degree = request.POST.get("degree")
                year = request.POST.get("degree_year")
                dob = request.POST.get("dob")
                if not dob:
                    dob="2000-01-01"
                all_authenticated_users = User.objects.all()
                all_existing_usernames = [u.username for u in all_authenticated_users]
                all_existing_emails = [u.email for u in all_authenticated_users]
                if name=="" or email=="":
                    messages.error(request, "Please fill all required fields i.e., name, email and password")
                else:
                    if email in all_existing_emails:
                        u = Users.objects.filter(email=email)
                        if u:
                            messages.error(request, "Email Already Exists. Please a different email.")
                        else:
                            usr = Users(name=name, email=email, phone=phone, degree=degree, year=year, dob=dob, allowed_test=json.dumps([]), username="", password="", is_active=True)
                            usr.save()
                            messages.error(request, "Email Already Exists. Please a different email.")
                    else:
                        username = email.split("@")[0]
                        while username in all_existing_usernames:
                            username = username + str(random.randint(0, 1000))
                        try:
                            password = generate_passwrod()
                            a_user= User.objects.create_user(username=username,
                                                                 email=email,
                                                                 password=password)
                            if a_user:
                                usr = Users(name=name, email=email, phone=phone, degree=degree, year=year, dob=dob, allowed_test=json.dumps([]), username=username, password=password, is_active=True)
                                usr.save()
                                messages.success(request, "User Created. Username(without qutations): '"+username+"' Password(without qutations): '"+password+"'")
                            else:
                                messages.error(request, "Unable to create User.")
                        except:
                            messages.error(request, "Unable to create User.")
            if "del_user" in request.POST:
                op = int(request.POST.get("del_user"))
                email = request.POST.get("email")
                del_flag = True
                try:
                    a_u = User.objects.get(email = email)
                    a_u.delete()
                except:
                    del_flag = False
                try:
                    u = Users.objects.filter(email=email)[0]
                    u.is_active=False
                    u.save()
                    messages.success(request, "The user is deleted")
                except:
                    del_flag = False
                if not del_flag:
                    messages.error(request, "Unable to delete")
            if "assign_user" in request.POST:
                op = int(request.POST.get("assign_user"))
                email = request.POST.get("email")
                t_id = request.POST.get("t_id")
                u = Users.objects.filter(email=email)
                if u:
                    try:
                        u = u[0]
                        u.is_active = True
                        u.allowed_test = json.dumps(list(set(json.loads(u.allowed_test)+[t_id])))
                        u.save()
                        messages.success(request, "Test is assigned!")
                    except:
                        messages.error(request, "User not found!")
                else:
                    messages.error(request, "User not found!")
            if "assign_batch" in request.POST:
                try:
                    op = int(request.POST.get("assign_batch"))
                    b_id = request.POST.get("b_id")
                    t_id = request.POST.get("t_id")
                    b = Batches.objects.filter(b_id=b_id)[0]
                    u_emails = json.loads(b.u_ids)
                    done_e, error_e = [], []
                    for email in u_emails:
                        try:
                            u = Users.objects.filter(email=email)
                            if u:
                                try:
                                    u = u[0]
                                    u.is_active = True
                                    print(t_id)
                                    print(u.name, u.allowed_test)
                                    u.allowed_test = json.dumps(list(set(json.loads(u.allowed_test)+[t_id])))
                                    print(u.name, u.allowed_test)
                                    u.save()
                                except:
                                    error_e += [email]
                                done_e += [email]
                        except:
                            error_e += [email]
                    messages.success(request, "done for"+str(done_e)+(" failed for"+str(error_e) if error_e else ""))
                except:
                    messages.error(request, "Unable to Assign!")
            if "create_batch" in request.POST:
                try:
                    op = int(request.POST.get("create_batch"))
                    batch_name = request.POST.get("batch_name")
                    all_batches = Batches.objects.all()
                    batches = [b.b_id for b in all_batches if b.is_open]
                    if batch_name:
                        if batch_name not in batches:
                            csv_file = request.FILES["csv"]
                            df = pd.read_csv(io.BytesIO(csv_file.read()))
                            df = df.fillna("")
                            all_authenticated_users = User.objects.all()
                            all_existing_usernames = [u.username for u in all_authenticated_users]
                            all_existing_emails = [u.email for u in all_authenticated_users]
                            emails_to_add = []
                            status_dict = {"name":[],"email":[],"password":[],"remarks":[]}
                            for i in range(len(df)):
                                p, s = "", "Failed"
                                row = df.iloc[i]
                                name = row["name"]
                                email = row["email"]
                                phone = row["phone"]
                                dob = row["dob"]
                                degree = row["degree"]
                                year = row["year"]
                                username = email.split("@")[0]
                                while username in all_existing_usernames:
                                    username = username + str(random.randint(0, 1000))
                                password = generate_passwrod()
                                if not dob:
                                    dob="2000-01-01"
                                try:
                                    if email in all_existing_emails:
                                        p = ""
                                        s = "Previous user. Use previous password to login"
                                    else:
                                        a_user= User.objects.create_user(username=username,
                                                                                 email=email,
                                                                                 password=password)
                                        if a_user:
                                            p = password
                                            s = "New user"
                                        else:
                                            p = ""
                                            s = "Failed"
                                    u = Users.objects.filter(email=email)
                                    if u:
                                        u = u[0]
                                        u.password = password
                                        u.is_active = True
                                        u.save()
                                    else:
                                        usr = Users(name=name, email=email, phone=phone, degree=degree, year=year, dob=dob, allowed_test=json.dumps([]), username=username, password=password, is_active=True)
                                        usr.save()
                                except:
                                    p, s = "", "Failed"
                                status_dict["name"] += [name]
                                status_dict["email"] += [email]
                                status_dict["password"] += [p]
                                status_dict["remarks"] += [s]
                                if s!="Failed":
                                    emails_to_add += [email]

                            df = pd.DataFrame.from_dict(status_dict)
                            b = Batches(b_id=batch_name, u_ids=json.dumps(emails_to_add), is_open=True)
                            b.save()
                            messages.success(request, "Batch saved succesfully")
                            return download_df_as_csv(df,batch_name+".csv")
                        else:
                            messages.error(request, "Batch name already exists!")
                    else:
                        messages.error(request, "Batch name is required!")
                except:
                    messages.error(request, "Error Occured!")
            if "delete_batch" in request.POST:
                op = int(request.POST.get("delete_batch"))
                b_id = request.POST.get("b_id")
                b = Batches.objects.filter(b_id=b_id)
                if b:
                    try:
                        b = b[0]
                        b.is_open = False
                        b.save()
                        all_batches = Batches.objects.all()
                        batches = [b.b_id for b in all_batches if b.is_open]
                    except:
                        messages.error(request, "Batch not found!")
                else:
                    messages.error(request, "Batch not found!")
    except:
        print(traceback.print_exc())
    return render(
        request,
        'users_m.html',
        {
            "op":op,
            "all_t_ids":all_t_ids,
            "batches":batches
        }
    )

def results(request, op=2):
    if not request.META.get('HTTP_REFERER'):
        return redirect(index)
    if not request.user.is_authenticated:
        return redirect(index)
    try:
        tests = Tests.objects.all()
        t_ids = [t.t_id for t in tests if t.is_open]
        all_batches = Batches.objects.all()
        b_ids = [b.b_id for b in all_batches if b.is_open]
        superuserflag = False
        search = ""
        username = request.user.username
        if request.user.is_superuser:
            email = username+"@super.user"
            superuserflag = True
        else:
            u = Users.objects.filter(username=username)[0]
            email = u.email
        if request.method == "POST":
            if "by_t_link" in request.POST:
                op = 1
            if "by_e_link" in request.POST:
                op = 2
            if "search_email" in request.POST or "download_email" in request.POST:
                if "search_email" in request.POST:
                    op = int(request.POST.get("search_email"))
                if "download_email" in request.POST:
                    op = int(request.POST.get("download_email"))
                email = request.POST.get("email")
                print(email)
            if "search_test" in request.POST or "download_test" in request.POST:
                if "search_test" in request.POST:
                    op = int(request.POST.get("search_test"))
                if "download_test" in request.POST:
                    op = int(request.POST.get("download_test"))
                t_id = request.POST.get("t_id")
                b_id = request.POST.get("b_id")
                print(t_id,b_id)
    except:
        print(traceback.print_exc())
    return render(
        request,
        'results.html',
        {
            "op": op,
            "email": email,
            "superuserflag": superuserflag,
            "t_ids": t_ids,
            "b_ids": b_ids,
            "search": search
            
        }
    )




