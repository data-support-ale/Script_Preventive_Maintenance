import { Injectable } from "@angular/core";
import {
  HttpClient,
  HttpErrorResponse,
  HttpHeaders,
  HttpClientXsrfModule,
  HttpXsrfTokenExtractor,
} from "@angular/common/http";
import { Observable, throwError, BehaviorSubject } from "rxjs";
import { retry, catchError, tap } from "rxjs/operators";
import { map } from "rxjs/operators";
import { User } from "../../models/user";


export class HttpService<T> {
  private currentUserSubject: BehaviorSubject<User>;
  public currentUser: Observable<User>;
  public token: string;
  private xsrf: string;
  public isLoggedIn: boolean = false;
  constructor(
    private httpClient: HttpClient,
    private url: string,
    private endpoint: string,
    private tokenExtractor?: HttpXsrfTokenExtractor
  ) {
    this.currentUserSubject = new BehaviorSubject<User>(
      JSON.parse(localStorage.getItem("currentUser") || "{}")
    );
    this.xsrf = this.tokenExtractor?.getToken() || "";
    this.currentUser = this.currentUserSubject.asObservable();
  }

  httpOptions = {

    headers: new HttpHeaders({
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      'X-CSRFToken': localStorage.getItem('csrfToken')
    }),
  };

  httpOptionsMultipart = {
    headers: new HttpHeaders({
      "Content-Type": "multipart/form-data;boundary=----WebKitFormBoundaryyrV7KO0BoCBuDbTL",
      "Access-Control-Allow-Origin": "*",
      'X-CSRFToken': localStorage.getItem('csrfToken')
    }),
  };

  getUser(): Observable<T[]> {
    return this.httpClient
      .get<T[]>(`${this.url}/users/`, this.httpOptions)
      .pipe(catchError(this.handleError));
  }

  get(): Observable<T[]> {
    return this.httpClient
      .get<T[]>(`${this.url}/${this.endpoint}`, this.httpOptions)
      .pipe(catchError(this.handleError));
  }

  getAbout(): Observable<T[]> {
    return this.httpClient
      .get<T[]>(`${this.url}/${this.endpoint}`)
      .pipe(catchError(this.handleError));
  }

  getDownload() {
    return this.httpClient
      .get(`${this.url}/${this.endpoint}`, { responseType: 'text' })
  }

  getAleUpgrade() {
    return this.httpClient
      .get(`${this.url}/ale-upgrade/`, { responseType: 'text' })
  }

  getById(id: number): Observable<T> {
    return this.httpClient
      .get<T>(`${this.url}/${this.endpoint}/${id}`)
      .pipe(retry(1), catchError(this.handleError));
  }

  testconnection(item: T): Observable<T> {
    return this.httpClient
      .post<T>(
        `${this.url}/testconnection/`,
        JSON.stringify(item),
        this.httpOptions
      )
      .pipe(catchError(this.handleError));
  }
  postFile(item: any): Observable<T> {
    return this.httpClient
      .post<T>(
        `${this.url}/upload-offline/`,
        JSON.stringify(item),
        this.httpOptionsMultipart
      )
      .pipe(catchError(this.handleError));
  }

  post(item: T): Observable<T> {
    return this.httpClient
      .post<T>(
        `${this.url}/${this.endpoint}`,
        JSON.stringify(item),
        this.httpOptions
      )
      .pipe(catchError(this.handleError));
  }

  postByValue(item: T, pramms: any): Observable<T> {
    return this.httpClient
      .post<T>(
        `${this.url}/${this.endpoint}/${pramms}`,
        JSON.stringify(item),
        this.httpOptions
      )
      .pipe(catchError(this.handleError));
  }

  updateProfile(item: T): Observable<T> {
    return this.httpClient
      .put<T>(
        `${this.url}/${this.endpoint}`,
        JSON.stringify(item),
        this.httpOptions,
      )
      .pipe(retry(1), catchError(this.handleError));
  }

  update(itemID: any, item: T): Observable<T> {
    return this.httpClient
      .put<T>(
        `${this.url}/${this.endpoint}/${itemID}`,
        JSON.stringify(item),
        this.httpOptions,
      )
      .pipe(retry(1), catchError(this.handleError));
  }

  patch(itemID: any, item: T): Observable<T> {
    return this.httpClient
      .patch<T>(
        `${this.url}/${this.endpoint}/${itemID}`,
        JSON.stringify(item),
        this.httpOptions
      )
      .pipe(retry(1), catchError(this.handleError));
  }

  patchEnable(itemID: any, item: T): Observable<T> {
    return this.httpClient
      .patch<T>(
        `${this.url}/${this.endpoint}/enable`,
        JSON.stringify(item),
        this.httpOptions
      )
      .pipe(retry(1), catchError(this.handleError));
  }

  delete(item: T) {
    return this.httpClient
      .delete<T>(`${this.url}/${this.endpoint}/${item}`, this.httpOptions)
      .pipe(retry(1), catchError(this.handleError));
  }

  login(username: string, password: string) {
    localStorage.removeItem("currentUser");
    localStorage.removeItem('csrfToken');
    localStorage.clear();
    localStorage.setItem('csrfToken', null);
    this.token = null;
    return this.httpClient
      .post<any>(`${this.url}/login`, { username, password }, {
        headers:
          new HttpHeaders({ 'Content-Type': 'application/json' })
      })
      .pipe(
        map((user: any) => {
          // store user details and basic auth credentials in local storage to keep user logged in between page refreshes
          if (user.Status === "Success") {
            user.authdata = window.btoa(username + ":"); //removed password for security reasons
            localStorage.setItem("currentUser", JSON.stringify(user));
            const xsrfCookies = document.cookie.split(';')
              .map(c => c.trim())
              .filter(c => c.startsWith('csrftoken='));
            document.cookie = "csrftoken=" + xsrfCookies[0].split('=')[1];
            localStorage.setItem('csrfToken', xsrfCookies[0].split('=')[1])
            localStorage.setItem('currentEmail', user.user_email);
            this.isLoggedIn = true;
            this.currentUserSubject.next(user);
            if (user.type_name === "Admin") {
              localStorage.setItem("isAdmin", "Yes")
            } else {
              localStorage.setItem("isAdmin", "No")
            }
            return user;
          }
        }),
        catchError(this.handleError)
      );
  }

  logout() {
    // remove user from local storage to log user out
    localStorage.removeItem("currentUser");
    localStorage.removeItem("csrfToken");
    localStorage.clear();

    this.currentUserSubject.next({} as User);

    return this.httpClient
      .get<T[]>(`${this.url}/logout`)
      .pipe(retry(1), catchError(this.handleError));
  }

  public get isUserLogged(): boolean {
    return this.isLoggedIn;
  }
  public get currentUserValue(): User {
    return this.currentUserSubject.value;
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = "";

    if (error.error instanceof ErrorEvent) {
      //error client
      errorMessage = error.error.message;
    } else {
      //error server
      errorMessage =
        `Error code: ${error.status}, ` + `message: ${error.message}`;
    }

    return throwError(errorMessage);
  }
}
