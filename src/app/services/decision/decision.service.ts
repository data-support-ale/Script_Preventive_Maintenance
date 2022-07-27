import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { HttpService } from "../../services/http/http.service";
import { environment } from "./../../../environments/environment";
import { Decision } from "../../models/decision";

@Injectable({
  providedIn: "root",
})
export class DecisionService extends HttpService<Decision> {
  constructor(httpClient: HttpClient) {
    super(httpClient, environment.restURL, environment.decision);
  }
}
