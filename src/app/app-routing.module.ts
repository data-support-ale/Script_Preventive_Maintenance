import { formatPercent } from "@angular/common";
import { NgModule } from "@angular/core";
import { RouterModule, Routes } from "@angular/router";
import { DashboardComponent } from "./dashboard/dashboard.component";
import { DecisionComponent } from "./decision/decision.component";
import { LoginComponent } from "./login/login.component";
import { RulesComponent } from "./rules/rules.component";
import { SettingsComponent } from "./settings/settings.component";
import { StatisticsComponent } from "./statistics/statistics.component";
import { AuthGuard } from "./helpers/auth.guard";
import { EditProfileComponent } from "./edit-profile/edit-profile.component";
import { PageNotFoundComponent } from "./pageNotFound/page-not-found/page-not-found.component";
import { LogoutComponent } from "./logout/logout/logout.component";
import { HeaderComponent } from "./header/header.component";

const routes: Routes = [
  { path: "login", component: LoginComponent },
  { path: '', component: LoginComponent },
  { path: "logout", component: LogoutComponent },
  {
    path: "dashboard",
    component: DashboardComponent,
    canActivate: [AuthGuard],
  },
  { path: "rules", component: RulesComponent, canActivate: [AuthGuard] },
  {
    path: "statistics",
    component: StatisticsComponent,
    canActivate: [AuthGuard],
  },
  { path: "editprofile", component: EditProfileComponent, canActivate: [AuthGuard] },
  { path: "decision", component: DecisionComponent, canActivate: [AuthGuard] },
  { path: "settings", component: SettingsComponent, canActivate: [AuthGuard] },
  //{ path: "", redirectTo: "/login", pathMatch: "full" },
  { path: "**", component: PageNotFoundComponent },

];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule { }
