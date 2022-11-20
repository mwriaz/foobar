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
            print(username,password)
            user = authenticate(request, username=username, password=password)
            print("user:",user)
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
    return render(request, 'tests.html', {})

def take_test(request):
    if not request.META.get('HTTP_REFERER'):
        return redirect(index)
    if not request.user.is_authenticated:
        return redirect(index)
    return render(request, 'take_test.html', {})

def users_m(request):
    try:
        if not request.META.get('HTTP_REFERER'):
            return redirect(index)
        if not request.user.is_authenticated:
            return redirect(index)
        tests = Tests.objects.all()
        all_t_ids = [t.t_id for t in tests]
        batches = ["1","training1"]
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
                all_authenticated_users = User.objects.all()
                all_existing_usernames = [u.username for u in all_authenticated_users]
                all_existing_emails = [u.email for u in all_authenticated_users]
                if name=="" or email=="":
                    messages.error(request, "Please fill all required fields i.e., name, email and password")
                else:
                    if email in all_existing_emails:
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
#                 Batches(b_id="name", u_ids=json.dumps(['user1','user2']),is_open=True)
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
            if "assign_batch" in request.POST:
                op = int(request.POST.get("assign_batch"))
            if "create_batch" in request.POST:
                op = int(request.POST.get("create_batch"))
                csv_file = request.FILES["csv"]
                df = pd.read_csv(io.BytesIO(csv_file.read()))
            if "delete_batch" in request.POST:
                op = int(request.POST.get("delete_batch"))
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

def results(request):
    if not request.META.get('HTTP_REFERER'):
        return redirect(index)
    if not request.user.is_authenticated:
        return redirect(index)
    return render(request, 'results.html', {})





