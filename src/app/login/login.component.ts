import { Component, OnInit } from "@angular/core";
import { Router } from "@angular/router";
import { LoginService } from "../services/login.service";
import { FormBuilder, FormGroup, Validators } from "@angular/forms";
import { Login } from "../models/login";
import { LogoutService } from "../services/logout.service";

@Component({
  selector: "app-login",
  templateUrl: "./login.component.html",
  styleUrls: ["./login.component.css"],
})
export class LoginComponent implements OnInit {
  login = {} as Login;
  loginForm!: FormGroup;
  submitted: boolean = false;
  error: boolean = false;
  remindMe: boolean = false;

  constructor(
    private router: Router,
    private loginService: LoginService,
    private formBuilder: FormBuilder,
    private logoutService: LogoutService
  ) {

    try {
      this.loginService.getUser().subscribe(

        (data: any) => {
          if (localStorage.getItem('currentUser') && (localStorage.getItem("remindMe") === 'true')) {
            this.router.navigate(["/rules"]);
          } else {
            localStorage.clear();
            this.logoutService.logoutForApp().subscribe(
              (response) => {
                this.router.navigate(["/login"])
              },
              (error) => console.log(error)
            );
          }
        },
        (error: any) => {
          this.router.navigate(["/login"]);
        }
      );
    } catch (err) {
      this.router.navigate(["/login"]);
    }

  }

  remindMeHandler(e: any): void {
    if (e.target.checked) {
      this.remindMe = true;
    } else {
      this.remindMe = false;
    }
  }

  ngOnInit(): void {
    // localStorage.clear();
    this.loginForm = this.formBuilder.group({
      username: ["", [Validators.required, Validators.email]],
      password: ["", [Validators.required]],
    });
  }

  get f() {
    return this.loginForm.controls;
  }

  OnSubmit() {
    this.submitted = true;
    // stop here if form is invalid
    if (this.loginForm.invalid) {
      return;
    }
    //this.loginForm.value
    this.loginService
      .login(this.loginForm.value.username, this.loginForm.value.password)
      .subscribe(
        (data: any) => {
          this.error = false;
          if (this.remindMe) {
            localStorage.setItem("remindMe", "true")
          } else {
            localStorage.setItem("remindMe", "false")
          }
          this.router.navigate(["/rules"]);
        },
        (error: any) => {
          this.error = true;
        }
      );
  }
  onReset(): void {
    this.submitted = false;
    this.loginForm.reset();
  }
}
