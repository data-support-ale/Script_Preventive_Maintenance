import { Injectable } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { HttpService } from "../../services/http/http.service";
import { environment } from "./../../../environments/environment";
import { Rule } from "../../models/rule";

@Injectable({
  providedIn: 'root'
})

export class RuleService extends HttpService<Rule>{
  constructor(httpClient: HttpClient) {
    super(httpClient, environment.restURL, environment.rules);
  }

  getRules() {
    return this.get();
  }

  addRule(ruleData: Rule) {
    return this.post(ruleData);
  }
  editRule(id: any, ruleData: Rule) {
    return this.update(id, ruleData);
  }
  deleteRule(ruleId: any) {
    return this.delete(ruleId);
  }
  enableRules(id: any, ruleData: Rule) {
    return this.patchEnable(id, ruleData);

  }
}

