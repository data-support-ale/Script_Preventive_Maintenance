import { Injectable } from "@angular/core";
import { Login } from "../models/login";
import { Observable, throwError, BehaviorSubject } from "rxjs";
import { catchError, retry } from "rxjs/operators";
import { HttpClient } from "@angular/common/http";
import { HttpService } from "../services/http/http.service";
import { environment } from "./../../environments/environment";

@Injectable({
  providedIn: "root",
})
export class LoginService extends HttpService<Login> {
  constructor(httpClient: HttpClient) {
    super(httpClient, environment.restURL, environment.login);
  }

}
