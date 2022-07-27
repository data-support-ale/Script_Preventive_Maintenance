import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Location } from '@angular/common'
import { LogoutService } from 'src/app/services/logout.service';
declare var $: any;

@Component({
  selector: 'app-logout',
  templateUrl: './logout.component.html',
  styleUrls: ['./logout.component.css']
})
export class LogoutComponent implements OnInit {
  isIdle: boolean = false;

  constructor(private logoutService: LogoutService, public router: Router, private location: Location) {

    if (this.router.getCurrentNavigation().extras.state) {
      this.isIdle = this.router.getCurrentNavigation().extras.state['flag'];
    }

  }


  ngOnInit(): void {
    //$("#logoutModel").modal("show");
  }
  ngAfterViewInit() {
    setTimeout(() => {
      if (!this.isIdle) {
        $("#logoutModelShow").modal("show");
      } else {
        this.logout();
      }
    })
  }

  cancel() {
    this.location.back();
  }

  delete_cookie() {
    document.cookie = 'csrftoken=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  }
  logout() {
    if (localStorage.getItem("currentUser")) {
      this.delete_cookie();
      localStorage.clear();
      this.logoutService.logoutForApp().subscribe(
        (response) => {
          $("#logoutModelShow").modal("hide");
          this.router.navigate(["/login"])
            .then(() => {
              window.location.reload();
            });
        },
        (error) => console.log(error)
      );
    } else {
      this.delete_cookie();
      localStorage.clear();
      $("#logoutModelShow").modal("hide");
      this.router.navigate(["/login"])
    }
  }
}
