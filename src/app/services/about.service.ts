import { Injectable } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { HttpService } from "./http/http.service";
import { Aboutus } from "../models/aboutus"
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AboutService extends HttpService<AboutService>  {

  constructor(httpClient: HttpClient) {
    super(httpClient, environment.restURL, environment.about)

  }

  getAboutUs() {
    return this.getAbout();
  }

  upgradeFromOffline() {
    // return this.post();
  }
}
