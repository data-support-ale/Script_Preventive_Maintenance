import { Component, ComponentFactoryResolver, ViewChild, ElementRef, HostListener, OnInit } from "@angular/core";
import { LoginService } from "../services/login.service";
import { User } from "../models/user";
import { FormGroup, FormBuilder, FormControl, Validators } from '@angular/forms';
import Swal from 'sweetalert2';
import {
  HttpClient,
  HttpHeaders
} from "@angular/common/http";
import {
  Router,
  NavigationStart,
  NavigationEnd,
  Event as NavigationEvent,
} from "@angular/router";
import { AboutService } from "../services/about.service";
import { downloadService } from "../services/download.service";
import { HttpService } from "../services/http/http.service";
import { AuthService } from "../services/auth.service";
import { NgxSpinnerService } from "ngx-spinner";
declare var $: any;

export interface TabItem {
  label: string;
  route: string;
  icon: string;
  activeIcon: string;
}
export interface MatMenuListItem {
  menuLinkText: string;
  menuIcon: string;
}

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})


export class HeaderComponent implements OnInit {


  @ViewChild('myInput')
  myInputVariable: ElementRef;
  isLoggedin = false;
  currentUser: User = {} as User;
  aboutObject: any;
  fileObject: any;
  token: any = null;
  zipFiles: File;
  form: FormGroup;
  downloadObject: any;
  loginDataName: any;
  menuVariable: boolean = false;
  menu_icon_variable: boolean = false;
  menu_res: boolean = true;
  constructor(
    private https: AuthService,
    public router: Router,
    private loginService: LoginService,
    private aboutservice: AboutService,
    private downloadservice: downloadService,
    public fb: FormBuilder,
    private spinner: NgxSpinnerService,
    private http: HttpClient
  ) {
    this.form = this.fb.group({
      avatar: [null]
    })

    this.loginService.currentUser.subscribe((x: any) => (this.currentUser = x));
    const loginData = JSON.parse(localStorage.getItem("currentUser"));
    this.loginDataName = loginData.user_name.charAt(0).toUpperCase();

  }

  ngOnInit(): void {
    //Start watching for user inactivity.
    if (localStorage.getItem("currentUser")) {
      this.isLoggedin = true;
      // this.router.navigate(["/rules"]);
    } else {
      this.isLoggedin = false;
    }

  }

  openMenu() {
    this.menuVariable = !this.menuVariable;
    this.menu_icon_variable = !this.menu_icon_variable;
    this.menu_res = !this.menu_res;
  }
  title = "ALE Logger";

  menuListItems: MatMenuListItem[] = [
    {
      menuLinkText: "Edit Profile",
      menuIcon: "settings",
    },
    {
      menuLinkText: "About",
      menuIcon: "settings",
    },
    {
      menuLinkText: "Logout",
      menuIcon: "settings",
    },
  ];
  tabs: TabItem[] = [
    {
      label: "Rules",
      route: "/rules",
      icon: "Icon_rules.svg",
      activeIcon: "rules icon.png"
    },
    {
      label: "Statistics",
      route: "/statistics",
      icon: "Icon_statistics.svg",
      activeIcon: "Icon_statistics.png"
    },
    {
      label: "Decision",
      route: "/decision",
      icon: "Icon_decisions.svg",
      activeIcon: "Icon_decisions_page.svg"
    },
    {
      label: "Settings",
      route: "/settings",
      icon: "Icon_parametres.svg",
      activeIcon: "Icon_parametres.png"
    },
  ];


  idleLogout() {
    this.router.navigate(["/logout"], { state: { flag: true } })
  }

  logout() {
    this.router.navigate(["/logout"], { state: { flag: false } })
  }
  openAboutUsModal() {
    this.getAboutUs();
  }


  getAboutUs() {
    this.spinner.show();
    this.token = localStorage.getItem('csrfToken');
    this.aboutservice.getAboutUs().subscribe((res: any) => {
      this.spinner.hide();
      this.aboutObject = res;
      $("#aboutUsModal").modal("show");
    });
  }

  opendownloadModel() {
    this.getDownloadFile();
    $("#downloadModel").modal("show");
  }

  getDownloadFile() {
    this.downloadservice.getDownloadFile().subscribe((res: any) => {
      this.downloadObject = res;
      var a = document.createElement('a');
      var blob = new Blob([res], { 'type': 'application/octet-stream' });
      a.href = window.URL.createObjectURL(blob);
      a.download = 'timelog.log';
      a.click()
      $("#downloadModal").modal("hide");
    });
  }

  openOfflineUpgradeModel() {
    this.myInputVariable.nativeElement.value = "";
    $("#OfflineUpgradeModel").modal("show");
  }

  openAleRepoModel() {
    this.downloadservice.aleUpgrade().subscribe((res: any) => {
      Swal.fire({
        icon: 'success',
        title: 'Great',
        text: 'The application is successfully updated with the latest scripts from ALE Repository'
      })

    }, (err) => {
      Swal.fire({
        icon: 'error',
        title: 'Failure',
        text: 'An error occurred while updating the application with the latest scripts from ALE Repository'
      })
      console.log(err)
    });
  }

  uploadFile(event) {
    const file = (event.target as HTMLInputElement).files[0];
    this.form.patchValue({
      avatar: file
    });
    this.form.get('avatar').updateValueAndValidity()
  }

  httpOptionsMultipart = {
    headers: new HttpHeaders({
      'X-CSRFToken': this.token
    }),
  };

  submitForm() {
    var formData: any = new FormData();
    formData.append("script", this.form.get('avatar').value);
    this.http.post(`http://${window.location.hostname}:8000/api/upload-offline/`, formData, { headers: new HttpHeaders({ 'X-CSRFToken': localStorage.getItem('csrfToken') }) }).subscribe(
      (response) => {
        $("#OfflineUpgradeModel").modal("hide");
        Swal.fire('Thank you...', 'Your file got uploaded!', 'success');
      },
      (error) => console.log(error)
    )
  }

}
