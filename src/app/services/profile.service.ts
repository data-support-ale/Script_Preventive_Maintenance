import { Injectable } from "@angular/core";
import { Profile } from "../models/profile";
import { HttpClient } from "@angular/common/http";
import { HttpService } from "../services/http/http.service";
import { environment } from "./../../environments/environment";

@Injectable({
    providedIn: "root",
})
export class ProfileService extends HttpService<Profile> {

    constructor(httpClient: HttpClient) {
        super(httpClient, environment.restURL, environment.profile);
    }

    getProfile() {
        return this.get();
    }

    updates(profileData: Profile) {
        return this.updateProfile(profileData);
    }

    logoutFromProfile() {
        return this.logout();
    }
}
