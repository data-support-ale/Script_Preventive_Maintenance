import { NgModule } from "@angular/core";
import { BrowserModule } from "@angular/platform-browser";
import {
  HttpClientModule,
  HttpClientXsrfModule,
  HTTP_INTERCEPTORS,
} from "@angular/common/http";
import { CookieModule } from 'ngx-cookie';

import { AppRoutingModule } from "./app-routing.module";
import { AppComponent } from "./app.component";
import { LoginComponent } from "./login/login.component";
import { DashboardComponent } from "./dashboard/dashboard.component";
import { BrowserAnimationsModule } from "@angular/platform-browser/animations";
import { FlexLayoutModule } from "@angular/flex-layout";
import { FormsModule, ReactiveFormsModule } from "@angular/forms";
import { RulesComponent } from "./rules/rules.component";
import { StatisticsComponent } from "./statistics/statistics.component";
import { DecisionComponent } from "./decision/decision.component";
import { SettingsComponent } from "./settings/settings.component";
import { TableModule } from "primeng/table";
import { EditProfileComponent } from "./edit-profile/edit-profile.component";
import { HeaderInterceptor } from "../app/helpers/http.interceptors";
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatNativeDateModule } from "@angular/material/core";
import { MatInputModule } from '@angular/material/input';
import { PageNotFoundComponent } from './pageNotFound/page-not-found/page-not-found.component';
import { LogoutComponent } from './logout/logout/logout.component';
import { NgIdleKeepaliveModule } from '@ng-idle/keepalive'; // this includes the core NgIdleModule but includes keepalive providers for easy wireup
import { MomentModule } from 'angular2-moment';
import { HeaderComponent } from './header/header.component'; // optional, provides moment-style pipes for date formatting
import { NgxSpinnerModule } from "ngx-spinner";
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';

@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    DashboardComponent,
    RulesComponent,
    StatisticsComponent,
    DecisionComponent,
    SettingsComponent,
    EditProfileComponent,
    PageNotFoundComponent,
    LogoutComponent,
    HeaderComponent
  ],
  imports: [
    NgIdleKeepaliveModule.forRoot(),
    MomentModule,
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    NgxSpinnerModule,
    FlexLayoutModule,
    FormsModule,
    ReactiveFormsModule,
    TableModule,
    HttpClientModule,
    MatDatepickerModule,
    MatFormFieldModule,
    MatNativeDateModule,
    MatInputModule,
    MatToolbarModule,
    MatIconModule,
    MatSidenavModule,
    MatListModule,
    HttpClientXsrfModule.withOptions({
      cookieName: "XSRF-TOKEN",
      headerName: "X-XSRF-TOKEN",
    }),
    CookieModule.forRoot()
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: HeaderInterceptor, multi: true },
  ],
  bootstrap: [AppComponent],
})
export class AppModule { }
