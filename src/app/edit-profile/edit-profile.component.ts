import { Component, OnInit } from '@angular/core';
import { FormGroup, FormControl, Validators, FormBuilder } from '@angular/forms'
import { ProfileService } from '../services/profile.service';
import { LoginService } from "../services/login.service";
import Swal from 'sweetalert2';
import { Router } from "@angular/router";
import { LogoutService } from '../services/logout.service';
declare var $: any;

@Component({
  selector: 'app-edit-profile',
  templateUrl: './edit-profile.component.html',
  styleUrls: ['./edit-profile.component.css']
})
export class EditProfileComponent implements OnInit {
  editprofileForm: FormGroup;
  error: boolean = false;
  constructor(private fb: FormBuilder, public router: Router, private logoutService: LogoutService, private profileService: ProfileService, private loginService: LoginService) {

    this.editprofileForm = this.fb.group({
      name: new FormControl('', Validators.required),
      email: new FormControl('', [Validators.required, Validators.email]),
      rainbowJid: new FormControl('', [Validators.required, Validators.email, Validators.pattern("^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,4}$")])
    })
  }

  ngOnInit(): void {
    this.getProfile();
  }

  getProfile() {
    this.profileService.getProfile().subscribe((res: any) => {
      let value = {
        name: res.user.name,
        email: res.user.email_id,
        rainbowJid: res.user.rainbow_jid
      }
      this.editprofileForm.setValue(value);
    })
  }

  submitProfile() {
    let value = {
      "name": this.editprofileForm.value['name'],
      "email_id": this.editprofileForm.value['email'],
      "rainbow_jid": this.editprofileForm.value['rainbowJid']
    }
    let previousEmail = localStorage.getItem('currentEmail');

    this.profileService
      .updates(value)
      .subscribe(
        (data: any) => {
          this.error = false;
          if (this.editprofileForm.value['email'] === previousEmail) {
            Swal.fire('Thank you', 'Your Profile is Updated!', 'success')
            this.getProfile();
          } else {
            // this.profileService.logoutFromProfile().subscribe((res: any) => {

            localStorage.clear();
            this.logoutService.logoutForApp().subscribe(
              (res) => {
                localStorage.removeItem('csrfToken');
                Swal.fire('Your Profile Updated!', 'Please login with the updated email Id', 'success');

                this.router.navigate(["/login"])
                  .then(() => {
                    window.location.reload();
                  });
              }
            )

            // });

          }
        },
        (error: any) => {
          this.error = true;
        }
      );
  }
}
