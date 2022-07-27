import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from 'src/environments/environment';
import { HttpService } from './http/http.service';

@Injectable({
  providedIn: 'root'
})
export class LogoutService extends HttpService<any> {

  constructor(httpClient: HttpClient) {
    super(httpClient, environment.restURL, environment.logout);
  }

  logoutForApp() {
    return this.logout();
  }
}
